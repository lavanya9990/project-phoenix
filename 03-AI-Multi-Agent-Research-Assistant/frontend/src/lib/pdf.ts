import type { Research } from "@/lib/api";

type ReportSection = { heading: string; body: string };

function parseReport(markdown: string): { title: string; sections: ReportSection[] } {
  const title = markdown.match(/^#\s+(.+)$/m)?.[1]?.trim() || "Research Report";
  const sections = markdown.split(/\r?\n(?=##\s+)/).slice(1)
    .map((chunk) => {
      const [heading = "", ...body] = chunk.split(/\r?\n/);
      return { heading: heading.replace(/^##\s+/, "").trim(), body: body.join("\n").trim() };
    })
    .filter((section) => section.heading.toLowerCase() !== "sources");
  return { title, sections };
}

function cleanMarkdown(value: string): string {
  return value.replace(/^[-*]\s+/gm, "- ").replace(/\[([^\]]+)]\([^)]+\)/g, "$1").replace(/[*_`]/g, "").trim();
}

export async function exportResearchPdf(research: Research): Promise<void> {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF({ unit: "pt", format: "a4" });
  const { title, sections } = parseReport(research.final_report);
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 54;
  const contentWidth = pageWidth - margin * 2;
  const bottom = pageHeight - margin;
  let y = margin;

  const ensureSpace = (height: number) => {
    if (y + height > bottom) { pdf.addPage(); y = margin; }
  };
  const addHeading = (text: string, size = 15) => {
    ensureSpace(size + 18);
    pdf.setFont("helvetica", "bold"); pdf.setFontSize(size); pdf.setTextColor(23, 107, 80);
    pdf.text(text, margin, y); y += size + 12;
  };
  const addText = (text: string, options?: { indent?: number; bold?: boolean }) => {
    const indent = options?.indent || 0;
    pdf.setFont("helvetica", options?.bold ? "bold" : "normal"); pdf.setFontSize(10.5); pdf.setTextColor(23, 33, 29);
    const lines = pdf.splitTextToSize(cleanMarkdown(text), contentWidth - indent) as string[];
    for (const line of lines) { ensureSpace(15); pdf.text(line, margin + indent, y); y += 15; }
    y += 8;
  };

  pdf.setFont("helvetica", "bold"); pdf.setFontSize(23); pdf.setTextColor(23, 33, 29);
  const titleLines = pdf.splitTextToSize(title, contentWidth) as string[];
  pdf.text(titleLines, margin, y); y += titleLines.length * 27 + 10;
  pdf.setFont("helvetica", "normal"); pdf.setFontSize(10); pdf.setTextColor(102, 115, 109);
  pdf.text("Research topic", margin, y); y += 15;
  addText(research.topic, { bold: true });

  const summary = sections.find((section) => section.heading === "Executive Summary");
  if (summary) { addHeading(summary.heading); addText(summary.body); }
  addHeading("Research Plan");
  research.plan.forEach((item, index) => {
    addText(`${index + 1}. ${item.question}`, { bold: true });
    addText(item.rationale, { indent: 14 });
  });
  for (const section of sections.filter((item) => item !== summary)) { addHeading(section.heading); addText(section.body); }

  addHeading("Sources");
  research.sources.forEach((source, index) => {
    ensureSpace(46); addText(`${index + 1}. ${source.title}`, { bold: true });
    pdf.setFont("helvetica", "normal"); pdf.setFontSize(9); pdf.setTextColor(23, 107, 80);
    const linkLines = pdf.splitTextToSize(source.url, contentWidth - 14) as string[];
    for (const line of linkLines) { ensureSpace(13); pdf.textWithLink(line, margin + 14, y, { url: source.url }); y += 13; }
    y += 8;
  });

  const pageCount = pdf.getNumberOfPages();
  for (let page = 1; page <= pageCount; page += 1) {
    pdf.setPage(page); pdf.setFont("helvetica", "normal"); pdf.setFontSize(8); pdf.setTextColor(125, 135, 130);
    pdf.text(`Phoenix Research | ${page} / ${pageCount}`, margin, pageHeight - 24);
  }
  pdf.save(`phoenix-research-${research.research_id}.pdf`);
}

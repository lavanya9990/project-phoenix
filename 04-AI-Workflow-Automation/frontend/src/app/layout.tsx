import Link from "next/link";import "./globals.css";
export const metadata={title:"Phoenix Flow",description:"AI lead automation"};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><aside><div className="brand">PHOENIX <span>FLOW</span></div><nav><Link href="/">Dashboard</Link><Link href="/leads/new">Add lead</Link><Link href="/leads">All leads</Link></nav></aside><main>{children}</main></body></html>}

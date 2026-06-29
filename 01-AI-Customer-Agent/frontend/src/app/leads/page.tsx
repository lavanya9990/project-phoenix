"use client";

import { useEffect, useState } from "react";

type Lead = {
    name: string;
    phone: string;
    preferred_time: string;
    created_at: string;
    status: string;
};

type LeadsResponse = {
    count: number;
    leads: Lead[];
};

export default function LeadsPage() {
    const [leads, setLeads] = useState<Lead[]>([]);
    const [count, setCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    async function fetchLeads() {
        try {
            setIsLoading(true);
            setError("");

            const response = await fetch("http://127.0.0.1:8000/leads");

            if (!response.ok) {
                throw new Error("Failed to fetch leads");
            }

            const data: LeadsResponse = await response.json();

            setLeads(data.leads);
            setCount(data.count);
        } catch (error) {
            setError("Could not load leads. Please check if backend is running.");
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        fetchLeads();
    }, []);

    return (
        <main className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-5xl mx-auto">
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">
                                Leads Dashboard
                            </h1>
                            <p className="text-gray-600 mt-1">
                                Appointment leads collected by the chatbot
                            </p>
                        </div>

                        <button
                            onClick={fetchLeads}
                            className="bg-black text-white px-5 py-3 rounded-xl font-medium hover:bg-gray-800"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-white rounded-2xl shadow p-5">
                        <p className="text-sm text-gray-500">Total Leads</p>
                        <p className="text-3xl font-bold text-gray-900">{count}</p>
                    </div>

                    <div className="bg-white rounded-2xl shadow p-5">
                        <p className="text-sm text-gray-500">Source</p>
                        <p className="text-xl font-semibold text-gray-900">Chatbot</p>
                    </div>

                    <div className="bg-white rounded-2xl shadow p-5">
                        <p className="text-sm text-gray-500">Status</p>
                        <p className="text-xl font-semibold text-gray-900">Active</p>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                    {isLoading && (
                        <div className="p-6 text-gray-600">Loading leads...</div>
                    )}

                    {error && <div className="p-6 text-red-600">{error}</div>}

                    {!isLoading && !error && leads.length === 0 && (
                        <div className="p-6 text-gray-600">
                            No leads yet. Book an appointment through the chatbot first.
                        </div>
                    )}

                    {!isLoading && !error && leads.length > 0 && (
                        <table className="w-full text-left">
                            <thead className="bg-gray-900 text-white">
                                <tr>
                                    <th className="p-4">Name</th>
                                    <th className="p-4">Phone</th>
                                    <th className="p-4">Preferred Time</th>
                                    <th className="p-4">Status</th>
                                    <th className="p-4">Created At</th>
                                </tr>
                            </thead>

                            <tbody>
                                {leads.map((lead, index) => (
                                    <tr key={index} className="border-b hover:bg-gray-50">
                                        <td className="p-4 text-gray-900 font-medium">
                                            {lead.name}
                                        </td>
                                        <td className="p-4 text-gray-700">{lead.phone}</td>
                                        <td className="p-4 text-gray-700">
                                            {lead.preferred_time}
                                        </td>
                                        <td className="p-4">
                                            <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                                                {lead.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-600 text-sm">
                                            {lead.created_at}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </main>
    );
}
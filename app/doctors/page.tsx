"use client";

import React, { useMemo, useState } from 'react';
import doctorsData, { Doctor } from '../../data/doctors';
import DoctorCard from '../../components/DoctorCard';

export default function DoctorsPage() {
  const [query, setQuery] = useState('');
  const [specialty, setSpecialty] = useState('All');

  const specialties = useMemo(() => {
    const s = new Set<string>();
    doctorsData.forEach((d) => s.add(d.specialty));
    return ['All', ...Array.from(s).sort()];
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return doctorsData.filter((d) => {
      if (specialty !== 'All' && d.specialty !== specialty) return false;
      if (!q) return true;
      return d.name.toLowerCase().includes(q) || d.specialty.toLowerCase().includes(q);
    });
  }, [query, specialty]);

  async function handleBook(id: string) {
    const doc = doctorsData.find((d) => d.id === id);
    if (!doc) return alert('Doctor not found');

    const patient = window.prompt('Patient name (for booking):', 'Jane Doe')?.trim();
    if (!patient) return;

    const date = window.prompt('Date (YYYY-MM-DD):', new Date().toISOString().slice(0, 10))?.trim();
    if (!date) return;

    const time = window.prompt('Time (HH:MM, 24h):', doc.schedule?.[0]?.startTime ?? '09:00')?.trim();
    if (!time) return;

    try {
      const res = await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_name: patient, doctor_name: doc.name, date, time, reason: '' }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Booking failed');
      alert(`Booked: ${data.doctor_name} ${data.date} ${data.time} (id ${data.appointment_id})`);
    } catch (err: any) {
      alert('Booking error: ' + (err.message || String(err)));
    }
  }

  return (
    <main className="p-6">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">Our Doctors</h1>
        <p className="text-slate-600 mt-1">Browse specialists, check availability, and book appointments.</p>
      </header>

      <section className="mb-6 flex flex-col sm:flex-row sm:items-center sm:gap-4 gap-2">
        <div className="flex-1">
          <input
            aria-label="Search doctors"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or specialty"
            className="w-full px-4 py-2 border rounded-lg"
          />
        </div>

        <div className="flex gap-2 overflow-auto">
          {specialties.map((s) => (
            <button
              key={s}
              onClick={() => setSpecialty(s)}
              className={`px-3 py-1 rounded-full ${s === specialty ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-700'}`}
            >
              {s}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filtered.map((d: Doctor) => (
            <DoctorCard key={d.id} doctor={d} onBook={handleBook} />
          ))}
        </div>
      </section>
    </main>
  );
}

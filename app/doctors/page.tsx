"use client";

import React, { useMemo, useState, useRef, useEffect } from 'react';
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

  const [modalOpen, setModalOpen] = useState(false);
  const [selected, setSelected] = useState<Doctor | null>(null);
  const [patientName, setPatientName] = useState('');
  const [dateValue, setDateValue] = useState(new Date().toISOString().slice(0, 10));
  const [timeValue, setTimeValue] = useState('09:00');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const firstInputRef = useRef<HTMLInputElement | null>(null);

  function openBookingModal(id: string) {
    const doc = doctorsData.find((d) => d.id === id) || null;
    setSelected(doc);
    setPatientName('');
    setDateValue(new Date().toISOString().slice(0, 10));
    setTimeValue(doc?.schedule?.[0]?.startTime ?? '09:00');
    setReason('');
    setError(null);
    setModalOpen(true);
  }

  useEffect(() => {
    if (modalOpen) firstInputRef.current?.focus();
  }, [modalOpen]);

  async function submitBooking() {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_name: patientName, doctor_name: selected.name, date: dateValue, time: timeValue, reason }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Booking failed');
      alert(`Booked: ${data.doctor_name} ${data.date} ${data.time} (id ${data.appointment_id})`);
      setModalOpen(false);
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setSubmitting(false);
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
            <DoctorCard key={d.id} doctor={d} onBook={openBookingModal} />
          ))}
        </div>
      </section>

      {/* Booking modal */}
      {modalOpen && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/40" onClick={() => setModalOpen(false)} />
          <div className="relative bg-white rounded-2xl p-6 w-full max-w-xl shadow-lg">
            <h2 className="text-xl font-semibold">Book appointment with {selected.name}</h2>
            <p className="text-sm text-slate-600">{selected.specialty} · {selected.experience} yrs</p>

            <div className="mt-4 grid grid-cols-1 gap-3">
              <label className="flex flex-col">
                <span className="text-sm font-medium">Patient name</span>
                <input ref={firstInputRef} value={patientName} onChange={(e)=>setPatientName(e.target.value)} className="mt-1 px-3 py-2 border rounded" />
              </label>

              <div className="flex gap-2">
                <label className="flex-1 flex flex-col">
                  <span className="text-sm font-medium">Date</span>
                  <input type="date" value={dateValue} onChange={(e)=>setDateValue(e.target.value)} className="mt-1 px-3 py-2 border rounded" />
                </label>
                <label className="flex-1 flex flex-col">
                  <span className="text-sm font-medium">Time</span>
                  <input type="time" value={timeValue} onChange={(e)=>setTimeValue(e.target.value)} className="mt-1 px-3 py-2 border rounded" />
                </label>
              </div>

              <label className="flex flex-col">
                <span className="text-sm font-medium">Reason (optional)</span>
                <input value={reason} onChange={(e)=>setReason(e.target.value)} className="mt-1 px-3 py-2 border rounded" />
              </label>

              {error && <div className="text-sm text-red-600">{error}</div>}

              <div className="mt-4 flex items-center justify-end gap-2">
                <button onClick={()=>setModalOpen(false)} className="px-4 py-2 rounded border">Cancel</button>
                <button onClick={submitBooking} disabled={submitting || !patientName} className="px-4 py-2 bg-orange-500 text-white rounded disabled:opacity-60">
                  {submitting ? 'Booking...' : 'Confirm booking'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

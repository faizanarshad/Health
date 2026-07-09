"use client";

import Image from 'next/image';
import React from 'react';
import type { Doctor } from '../data/doctors';

type Props = {
  doctor: Doctor;
  onBook?: (id: string) => void;
  href?: string;
};

export default function DoctorCard({ doctor, onBook, href }: Props) {
  const availabilitySummary = doctor.schedule
    .slice(0, 2)
    .map((s) => `${s.day} ${s.startTime}`)
    .join(' • ');

  return (
    <div className="group relative bg-white dark:bg-slate-900 rounded-2xl shadow-sm border p-5 hover:shadow-lg transition-shadow w-full">
      <div className="flex items-start gap-4">
        <div className="flex-none w-16 h-16 rounded-full overflow-hidden bg-slate-100 flex items-center justify-center">
          {doctor.avatar ? (
            // next/image requires width/height
            <Image src={doctor.avatar} alt={`${doctor.name} avatar`} width={64} height={64} className="object-cover" />
          ) : (
            <span className="text-slate-700 font-bold">{doctor.name.split(' ').map(n=>n[0]).slice(0,2).join('')}</span>
          )}
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-900">{doctor.name}</h3>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-sm px-2 py-1 rounded-full bg-blue-50 text-blue-700 font-medium">{doctor.specialty}</span>
            <span className="text-sm text-slate-500">{doctor.experience} yrs</span>
          </div>

          <p className="mt-3 text-sm text-slate-600 line-clamp-2">{doctor.bio}</p>

          <div className="mt-4 text-sm text-slate-600">Availability: <span className="font-medium text-slate-800">{availabilitySummary || '—'}</span></div>
        </div>
      </div>

      {/* back / details reveal */}
      <div className="mt-4 hidden group-hover:block focus-within:block">
        <div className="mt-2 grid grid-cols-1 gap-2 text-sm">
          {doctor.schedule.map((s) => (
            <div key={`${doctor.id}-${s.day}`} className="flex justify-between">
              <div className="text-slate-700">{s.day}</div>
              <div className="text-slate-500">{s.startTime} — {s.endTime}</div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-3">
          {onBook ? (
            <button
              onClick={() => onBook(doctor.id)}
              className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-300"
            >
              Book Appointment
            </button>
          ) : (
            <a href={href || '#'} className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600">
              Book Appointment
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

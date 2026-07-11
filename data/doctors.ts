export type Doctor = {
  id: string;
  name: string;
  specialty: string;
  bio: string;
  experience: number;
  location?: string;
  avatar?: string;
  schedule: Array<{ day: string; startTime: string; endTime: string }>;
};

const doctors: Doctor[] = [
  {
    id: 'dr-amina-javed',
    name: 'Dr. Amina Javed',
    specialty: 'Family Medicine',
    bio: 'Provides comprehensive care for families and chronic conditions with a calm, patient-centered approach.',
    experience: 14,
    location: 'Karachi, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '09:00', endTime: '12:00' },
      { day: 'Wednesday', startTime: '13:00', endTime: '16:00' },
      { day: 'Friday', startTime: '10:00', endTime: '14:00' },
    ],
  },
  {
    id: 'dr-saad-ahmed',
    name: 'Dr. Saad Ahmed',
    specialty: 'Cardiology',
    bio: 'Expert in heart health, hypertension, and preventive cardiology for adult patients.',
    experience: 12,
    location: 'Lahore, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Tuesday', startTime: '09:30', endTime: '12:30' },
      { day: 'Thursday', startTime: '13:30', endTime: '17:00' },
    ],
  },
  {
    id: 'dr-zainab-bashir',
    name: 'Dr. Zainab Bashir',
    specialty: 'Pediatrics',
    bio: 'Specializes in pediatric wellness, immunizations, and developmental care for children and teens.',
    experience: 9,
    location: 'Islamabad, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '10:00', endTime: '13:00' },
      { day: 'Wednesday', startTime: '09:00', endTime: '12:00' },
      { day: 'Friday', startTime: '14:00', endTime: '17:00' },
    ],
  },
  {
    id: 'dr-omar-nazir',
    name: 'Dr. Omar Nazir',
    specialty: 'General Surgery',
    bio: 'Balances clinic consultations with procedural care, focusing on timely referrals and surgical planning.',
    experience: 16,
    location: 'Karachi, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Tuesday', startTime: '14:00', endTime: '17:00' },
      { day: 'Thursday', startTime: '10:00', endTime: '13:00' },
    ],
  },
  {
    id: 'dr-nadia-hussain',
    name: 'Dr. Nadia Hussain',
    specialty: 'Dermatology',
    bio: 'Offers skin care, acne management, and cosmetic dermatology recommendations with clear follow-up plans.',
    experience: 11,
    location: 'Lahore, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '13:00', endTime: '17:00' },
      { day: 'Thursday', startTime: '09:00', endTime: '12:00' },
    ],
  },
  {
    id: 'dr-khalid-raza',
    name: 'Dr. Khalid Raza',
    specialty: 'Neurology',
    bio: 'Provides diagnostic assessments for headaches, neuropathy, and movement disorders in adults.',
    experience: 13,
    location: 'Rawalpindi, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Wednesday', startTime: '10:00', endTime: '14:00' },
      { day: 'Friday', startTime: '09:00', endTime: '12:00' },
    ],
  },
  {
    id: 'dr-mariam-siddiqui',
    name: 'Dr. Mariam Siddiqui',
    specialty: 'Obstetrics & Gynecology',
    bio: 'Dedicated to women’s health, prenatal care, and reproductive wellness with supportive bedside care.',
    experience: 10,
    location: 'Karachi, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Tuesday', startTime: '09:00', endTime: '13:00' },
      { day: 'Friday', startTime: '13:00', endTime: '16:00' },
    ],
  },
  {
    id: 'dr-tahir-qureshi',
    name: 'Dr. Tahir Qureshi',
    specialty: 'ENT',
    bio: 'Treats sinus, ear, and throat conditions with same-day follow-up planning for persistent symptoms.',
    experience: 8,
    location: 'Peshawar, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '09:30', endTime: '12:30' },
      { day: 'Thursday', startTime: '14:00', endTime: '17:00' },
    ],
  },
  {
    id: 'dr-fatima-noor',
    name: 'Dr. Fatima Noor',
    specialty: 'Endocrinology',
    bio: 'Manages diabetes, thyroid conditions, and hormonal health with personalized care plans.',
    experience: 12,
    location: 'Islamabad, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '11:00', endTime: '15:00' },
      { day: 'Wednesday', startTime: '13:00', endTime: '16:00' },
    ],
  },
  {
    id: 'dr-bilal-javed',
    name: 'Dr. Bilal Javed',
    specialty: 'Gastroenterology',
    bio: 'Treats digestive health, IBS, and liver concerns using evidence-based evaluation and follow-up.',
    experience: 15,
    location: 'Lahore, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Tuesday', startTime: '10:00', endTime: '14:00' },
      { day: 'Friday', startTime: '09:00', endTime: '12:00' },
    ],
  },
  {
    id: 'dr-hassan-rizvi',
    name: 'Dr. Hassan Rizvi',
    specialty: 'Orthopedics',
    bio: 'Focused on joint pain, sports injuries, and rehabilitation planning for active patients.',
    experience: 13,
    location: 'Karachi, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Wednesday', startTime: '09:00', endTime: '13:00' },
      { day: 'Thursday', startTime: '14:00', endTime: '17:00' },
    ],
  },
  {
    id: 'dr-saira-khan',
    name: 'Dr. Saira Khan',
    specialty: 'Psychiatry',
    bio: 'Supports mental health, anxiety, and mood care with a thoughtful, confidential approach.',
    experience: 11,
    location: 'Islamabad, Pakistan',
    avatar: '/doctors/placeholder.svg',
    schedule: [
      { day: 'Monday', startTime: '14:00', endTime: '17:00' },
      { day: 'Friday', startTime: '09:00', endTime: '12:00' },
    ],
  },
];

export default doctors;

export type ChatHistoryItem = {
  id: string;
  patientName: string;
  doctorName: string;
  snippet: string;
  timestamp: string;
  status: 'New' | 'Follow-up' | 'Resolved';
};

const chatHistory: ChatHistoryItem[] = [
  {
    id: 'thread-1',
    patientName: 'Ayesha Khan',
    doctorName: 'Dr. Amina Javed',
    snippet: 'Can I switch my family medicine visit from 9am to 11am next Monday?',
    timestamp: 'Today, 09:15',
    status: 'Follow-up',
  },
  {
    id: 'thread-2',
    patientName: 'Zara Ali',
    doctorName: 'Dr. Zainab Bashir',
    snippet: 'My child is due for a vaccine; can I book a Tuesday slot?',
    timestamp: 'Yesterday, 16:40',
    status: 'New',
  },
  {
    id: 'thread-3',
    patientName: 'Ahmed Noor',
    doctorName: 'Dr. Saad Ahmed',
    snippet: 'I need a follow-up for my blood pressure review in late April.',
    timestamp: 'Today, 08:50',
    status: 'Resolved',
  },
  {
    id: 'thread-4',
    patientName: 'Mariam Yasmeen',
    doctorName: 'Dr. Mariam Siddiqui',
    snippet: 'Looking for a prenatal appointment after my last check-up.',
    timestamp: 'Today, 10:30',
    status: 'Follow-up',
  },
];

export default chatHistory;

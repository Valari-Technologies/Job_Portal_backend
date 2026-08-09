import React from 'react';

export default function RecentApplications() {
  const applications = [
    { id: 1, jobName: 'UI/UX Designer', appliedDate: '15 May 2024', status: 'Under Review' },
    { id: 2, jobName: 'Frontend Developer', appliedDate: '10 May 2024', status: 'Applied' },
    { id: 3, jobName: 'Product Manager', appliedDate: '05 May 2024', status: 'Under Review' },
    { id: 4, jobName: 'Data Analyst', appliedDate: '28 Apr 2024', status: 'Rejected' }
  ];

  return (
    <div className="bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between overflow-hidden hover:shadow-md transition-shadow select-none">
      
      {/* Title & View All */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-bold text-[#E29D29] tracking-tight">Recent Applications</h2>
        <button type="button" className="text-xs font-bold text-[#2563EB] hover:underline cursor-pointer focus:outline-none">
          View All
        </button>
      </div>

      {/* Table Area */}
      <div className="overflow-x-auto w-full">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#84A43C]/5 border-b border-slate-100">
              <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-slate-500">Job Name</th>
              <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-slate-500">Applied Date</th>
              <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-slate-500">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {applications.map((app) => {
              // Status Badge Configuration
              let badgeStyle = '';
              if (app.status === 'Under Review') {
                badgeStyle = 'bg-amber-100 text-amber-800 border border-amber-200';
              } else if (app.status === 'Applied') {
                badgeStyle = 'bg-blue-100 text-blue-800 border border-blue-200';
              } else if (app.status === 'Rejected') {
                badgeStyle = 'bg-rose-100 text-rose-800 border border-rose-200';
              }

              return (
                <tr key={app.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-4 px-4 text-sm font-bold text-slate-700">{app.jobName}</td>
                  <td className="py-4 px-4 text-sm text-slate-500 font-medium">{app.appliedDate}</td>
                  <td className="py-4 px-4">
                    <span className={`inline-block px-3 py-1 text-xs font-bold rounded-full ${badgeStyle}`}>
                      {app.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}

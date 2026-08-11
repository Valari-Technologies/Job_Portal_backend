import React from 'react';
import { 
  ArrowUpRight, 
  ChevronDown, 
  PlusCircle, 
  ClipboardList,
  Briefcase
} from 'lucide-react';

export default function HrDashboardHome() {
  const stats = [
    {
      title: 'My Jobs',
      value: '16',
      linkText: 'View and update listings →',
      avatars: [
        'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
        'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150'
      ],
      greenLink: true
    },
    {
      title: 'Open Jobs',
      value: '10',
      linkText: 'Explore now →',
      greenLink: false
    },
    {
      title: 'Closed Jobs',
      value: '6',
      linkText: 'View details →',
      greenLink: false
    },
    {
      title: 'New Applications',
      value: '24',
      linkText: "See what's live →",
      avatars: [
        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
        'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150',
        'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150'
      ],
      greenLink: true
    },
    {
      title: 'Accepted Candidates',
      value: '8',
      linkText: 'View confirmed hires →',
      greenLink: false
    },
    {
      title: 'Rejected Candidates',
      value: '5',
      linkText: 'View →',
      greenLink: false
    }
  ];

  const jobsData = [
    { name: 'UI/UX Designer', count: 120, max: 125, color: 'bg-[#4A7318]' },
    { name: 'Frontend Developer', count: 98, max: 125, color: 'bg-[#8CC63F]' },
    { name: 'Product Manager', count: 72, max: 125, color: 'bg-[#E29D29]' },
    { name: 'Data Analyst', count: 48, max: 125, color: 'bg-[#84A43C]' },
    { name: 'HR Executive', count: 30, max: 125, color: 'bg-[#096317]' }
  ];

  const statusData = [
    { label: 'Applied', value: '45%', color: 'text-blue-600', stroke: '#2563EB', radius: 56, offset: 45 },
    { label: 'Under Review', value: '25%', color: 'text-amber-500', stroke: '#F59E0B', radius: 46, offset: 25 },
    { label: 'Accepted', value: '15%', color: 'text-emerald-500', stroke: '#10B981', radius: 36, offset: 15 },
    { label: 'Rejected', value: '15%', color: 'text-rose-500', stroke: '#EF4444', radius: 26, offset: 15 }
  ];

  return (
    <div className="flex flex-col gap-6 w-full text-left">
      
      {/* Overview Header */}
      <div>
        <h1 className="text-5xl font-black text-slate-800 tracking-tight">Overview</h1>
        {/* Statistics Cards Grid */}
      <div className="grid grid-cols-1 min-[375px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white rounded-[24px] p-5 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[140px] relative hover:shadow-md transition-shadow select-none">
            <div className="flex justify-between items-start">
              <span className="text-sm font-bold text-slate-400">{stat.title}</span>
              <button className="w-7 h-7 rounded-full bg-[#84A43C]/10 flex items-center justify-center text-[#84A43C] hover:bg-[#84A43C]/20 transition-colors cursor-pointer focus:outline-none">
                <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-baseline gap-3 mt-2">
              <span className="text-4xl font-black text-slate-800 leading-none">{stat.value}</span>
              {stat.avatars && (
                <div className="flex -space-x-2 overflow-hidden">
                  {stat.avatars.map((av, index) => (
                    <img
                      key={index}
                      className="inline-block h-6 w-6 rounded-full ring-2 ring-white object-cover"
                      src={av}
                      alt="Candidate avatar"
                    />
                  ))}
                </div>
              )}
            </div>

            <span className={`text-[11px] font-bold mt-3 block truncate ${stat.greenLink ? 'text-[#84A43C]' : 'text-slate-400'}`}>
              {stat.linkText}
            </span>
          </div>
        ))}
      </div>

      {/* Charts Middle Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Chart: Applications per Job */}
        <div className="lg:col-span-7 bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[350px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-black text-[#84A43C]">Applications per Job</h3>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-100 rounded-full text-sm font-bold text-slate-500 hover:bg-slate-100 transition-colors cursor-pointer">
              <span>This Month</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Horizontal Bar Chart list */}
          <div className="flex-grow flex flex-col justify-center gap-4">
            {jobsData.map((job, idx) => (
              <div key={idx} className="flex items-center gap-4 text-sm">
                <span className="w-24 sm:w-28 font-bold text-slate-600 truncate">{job.name}</span>
                <div className="flex-grow bg-slate-100 h-2.5 rounded-full overflow-hidden relative">
                  <div 
                    className={`h-full ${job.color} rounded-full transition-all duration-500`}
                    style={{ width: `${(job.count / job.max) * 100}%` }}
                  />
                </div>
                <span className="w-8 font-black text-slate-800 text-right">{job.count}</span>
              </div>
            ))}
          </div>

          {/* X-Axis labels */}
          <div className="flex justify-between text-[10px] font-bold text-slate-400 pl-24 sm:pl-32 pr-8 pt-4 border-t border-slate-50 mt-4">
            <span>0</span>
            <span>25</span>
            <span>50</span>
            <span>75</span>
            <span>100</span>
            <span>125</span>
          </div>
        </div>

        {/* Right Chart: Application Status Distribution */}
        <div className="lg:col-span-5 bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[350px]">
          <h3 className="text-2xl font-black text-[#84A43C] mb-6">Application Status Distribution</h3>
          
          <div className="flex flex-col sm:flex-row items-center justify-around flex-grow gap-6 sm:gap-4">
            {/* SVG Concentric Rings Chart */}
            <div className="relative w-40 h-40 flex items-center justify-center shrink-0">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="56" fill="transparent" stroke="#F1F5F9" strokeWidth="6" />
                <circle cx="60" cy="60" r="46" fill="transparent" stroke="#F1F5F9" strokeWidth="6" />
                <circle cx="60" cy="60" r="36" fill="transparent" stroke="#F1F5F9" strokeWidth="6" />
                <circle cx="60" cy="60" r="26" fill="transparent" stroke="#F1F5F9" strokeWidth="6" />
                
                {statusData.map((ring, idx) => {
                  const circum = 2 * Math.PI * ring.radius;
                  const pctVal = parseInt(ring.value);
                  const strokeDashoffset = circum - (pctVal / 100) * circum;
                  return (
                    <circle
                      key={idx}
                      cx="60"
                      cy="60"
                      r={ring.radius}
                      fill="transparent"
                      stroke={ring.stroke}
                      strokeWidth="6"
                      strokeDasharray={circum}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      className="transition-all duration-700 ease-out"
                    />
                  );
                })}
              </svg>

              <div className="absolute flex flex-col items-center justify-center leading-none">
                <span className="text-3xl font-black text-slate-800">240</span>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">Total</span>
              </div>
            </div>

            {/* Legend List */}
            <div className="flex flex-col gap-2.5 text-xs font-bold text-slate-500">
              {statusData.map((item, idx) => {
                let dotColor = 'bg-blue-600';
                if (idx === 1) dotColor = 'bg-amber-500';
                if (idx === 2) dotColor = 'bg-emerald-500';
                if (idx === 3) dotColor = 'bg-rose-500';
                return (
                  <div key={idx} className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
                    <span className="w-24 text-left font-bold text-slate-600">{item.label}</span>
                    <span className="text-slate-800 font-extrabold text-right w-8">{item.value}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

      </div>      </div>

      {/* Bottom Columns Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Column 1: Latest Applications */}
        <div className="bg-white rounded-[32px] p-5 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[300px]">
          <div>
            <h4 className="text-xl font-black text-blue-600 mb-4 tracking-tight">Latest Applications</h4>
            <div className="flex flex-col gap-4">
              {[
                { name: 'Ananya Patel', role: 'UI/UX Designer', time: '10 min ago', img: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150' },
                { name: 'Vikram Singh', role: 'Product Manager', time: '1 hr ago', img: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150' },
                { name: 'Neha Gupta', role: 'Data Analyst', time: '2 hr ago', img: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150' }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between gap-2.5">
                  <div className="flex items-center gap-3">
                    <img src={item.img} alt={item.name} className="w-8 h-8 rounded-full object-cover border border-slate-100" />
                    <div className="leading-tight text-left">
                      <p className="text-base font-black text-slate-800">{item.name}</p>
                      <p className="text-sm font-bold text-slate-400">{item.role}</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold text-slate-400 whitespace-nowrap text-right">{item.time}</span>
                </div>
              ))}
            </div>
          </div>
          <button className="text-base font-extrabold text-blue-600 hover:underline mt-4 text-center cursor-pointer focus:outline-none">
            View All
          </button>
        </div>

        {/* Column 2: Recently Published Jobs */}
        <div className="bg-white rounded-[32px] p-5 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[300px]">
          <div>
            <h4 className="text-xl font-black text-blue-600 mb-4 tracking-tight">Recently Published Jobs</h4>
            <div className="flex flex-col gap-4">
              {[
                { name: 'Senior UI/UX Designer', time: '1 day ago' },
                { name: 'Frontend Developer', time: '2 days ago' },
                { name: 'Product Manager', time: '3 days ago' }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
                  <span className="text-base font-black text-slate-700 truncate">{item.name}</span>
                  <span className="text-sm font-bold text-rose-500 whitespace-nowrap text-right">{item.time}</span>
                </div>
              ))}
            </div>
          </div>
          <button className="text-base font-extrabold text-blue-600 hover:underline mt-4 text-center cursor-pointer focus:outline-none">
            View All
          </button>
        </div>

        {/* Column 3: Recently Updated Jobs */}
        <div className="bg-white rounded-[32px] p-5 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[300px]">
          <div>
            <h4 className="text-xl font-black text-blue-600 mb-4 tracking-tight">Recently Updated Jobs</h4>
            <div className="flex flex-col gap-4">
              {[
                { name: 'HR Executive', time: '5 min ago' },
                { name: 'Data Analyst', time: '1 hr ago' },
                { name: 'Marketing Manager', time: '2 hrs ago' }
              ].map((item, idx) => (
                <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
                  <span className="text-base font-black text-slate-700 truncate">{item.name}</span>
                  <span className="text-sm font-bold text-amber-500 whitespace-nowrap text-right">{item.time}</span>
                </div>
              ))}
            </div>
          </div>
          <button className="text-base font-extrabold text-blue-600 hover:underline mt-4 text-center cursor-pointer focus:outline-none">
            View All
          </button>
        </div>

        {/* Column 4: Quick Actions */}
        <div className="bg-white rounded-[32px] p-5 shadow-xs border border-slate-100 flex flex-col justify-between min-h-[300px]">
          <div>
            <h4 className="text-xl font-black text-[#84A43C] mb-4 tracking-tight">Quick Actions</h4>
            <div className="flex flex-col gap-4">
              {/* Create Job Button */}
              <button className="w-full flex items-center gap-3 p-3 bg-[#84A43C]/10 hover:bg-[#84A43C]/20 text-[#84A43C] rounded-2xl transition-all cursor-pointer text-left focus:outline-none">
                <PlusCircle className="w-7 h-7 shrink-0" />
                <span className="text-base font-black">Create Job</span>
              </button>
              {/* Review Applications Button */}
              <button className="w-full flex items-center gap-3 p-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 rounded-2xl transition-all cursor-pointer text-left focus:outline-none">
                <ClipboardList className="w-7 h-7 shrink-0" />
                <span className="text-base font-black">Review Applications</span>
              </button>
            </div>
          </div>
          <div className="h-4" />
        </div>

      </div>

    </div>
  );
}

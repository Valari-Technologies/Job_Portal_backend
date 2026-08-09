import React from 'react';
import { FileText, ClipboardList, Briefcase } from 'lucide-react';
import gif1 from '../../assets/canditate/canditate-card-1.gif';
import gif2 from '../../assets/canditate/canditate-card-2.gif';
import gif3 from '../../assets/canditate/canditate-card-3.gif';

export default function StatCard({ type, title, value, subtext, date }) {
  let iconBg = '';
  let icon = null;
  let gifSrc = null;
  let gifAlt = '';
  let gifClass = '';

  if (type === 'resume') {
    iconBg = 'bg-[#096317]'; // Forest green circle icon bg
    icon = <FileText className="w-5 h-5 text-white" />;
    gifSrc = gif1;
    gifAlt = 'Resume status illustration';
    // Clean responsive size class ensuring it scales down on iPad/mobile
    gifClass = 'w-24 sm:w-28 md:w-32 h-20 sm:h-24 md:h-[95px] object-contain shrink-0';
  } else if (type === 'applications') {
    iconBg = 'bg-[#3536da]'; // Bright blue circle icon bg
    icon = <ClipboardList className="w-5 h-5 text-white" />;
    gifSrc = gif2;
    gifAlt = 'Applications status illustration';
    gifClass = 'w-28 sm:w-32 md:w-36 h-24 sm:h-28 md:h-[105px] object-contain shrink-0';
  } else if (type === 'opportunities') {
    iconBg = 'bg-[#f7840c]'; // Bright orange circle icon bg
    icon = <Briefcase className="w-5 h-5 text-white" />;
    gifSrc = gif3;
    gifAlt = 'Opportunities status illustration';
    gifClass = 'w-28 sm:w-32 md:w-36 h-22 sm:h-26 md:h-[100px] object-contain shrink-0';
  }

  return (
    <div className="relative w-full min-h-[175px] mt-4 select-none filter drop-shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:drop-shadow-[0_8px_18px_rgba(0,0,0,0.06)] transition-all">
      
      {/* Outer White Lobe Tab (Curved Outline wrapping the circle icon) */}
      <div className="absolute -top-4 -left-4 w-[76px] h-[76px] bg-white rounded-full z-10 flex items-center justify-center" />

      {/* Circle Icon Badge sitting centered inside the white lobe */}
      <div className="absolute -top-2.5 -left-2.5 z-20">
        <div className={`w-13 h-13 ${iconBg} rounded-full flex items-center justify-center shadow-sm`}>
          {icon}
        </div>
      </div>

      {/* Top-Right fillet transition curve */}
      <div className="absolute top-0 left-[60px] w-4 h-4 bg-[radial-gradient(circle_at_top_left,transparent_12px,white_12px)] pointer-events-none z-10" />

      {/* Bottom-Left fillet transition curve */}
      <div className="absolute top-[60px] left-0 w-4 h-4 bg-[radial-gradient(circle_at_top_left,transparent_12px,white_12px)] pointer-events-none z-10" />

      {/* Main Card Body - Flex row layout ensures no overlaps on all screen sizes */}
      <div className="bg-white rounded-[40px] p-5 pt-8 pb-5 pl-4 min-h-[160px] flex items-center gap-3 relative z-0 w-full">
        
        {/* GIF Illustration Container */}
        <div className="flex items-center justify-center shrink-0">
          <img src={gifSrc} alt={gifAlt} className={gifClass} />
        </div>

        {/* Card Info Content - Left-aligned text column */}
        <div className="flex-grow flex flex-col justify-center text-left min-w-0 pr-1">
          {type === 'resume' ? (
            <div className="space-y-0.5">
              <h3 className="text-[15px] font-bold text-slate-800 leading-snug truncate">Resume Status</h3>
              <p className="text-[13px] font-extrabold text-[#84A43C] truncate">Resume Uploaded</p>
              <p className="text-[10px] font-semibold text-slate-400 truncate">Updated on 15 May 2024</p>
            </div>
          ) : type === 'applications' ? (
            <div className="space-y-0.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">You'</span>
              <p className="text-3xl font-black text-slate-800 leading-none">12</p>
              <button 
                type="button" 
                className="text-[11px] font-extrabold text-blue-600 hover:underline mt-1.5 focus:outline-none cursor-pointer text-left block truncate w-full"
              >
                View all applications
              </button>
            </div>
          ) : (
            <div className="space-y-0.5">
              <p className="text-3xl font-black text-slate-800 leading-none">45</p>
              <h3 className="text-[13px] font-bold text-slate-800 leading-snug truncate">Current Opportunities</h3>
              <p className="text-[11px] font-bold text-[#f7840c] truncate">New jobs this week</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

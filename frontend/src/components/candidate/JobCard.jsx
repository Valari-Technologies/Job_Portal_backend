import React from 'react';
import { Clock, Briefcase, MapPin } from 'lucide-react';
import bgCorner from '../../assets/canditate/canditate-job-card-bgimage.png';

export default function JobCard({ title, department, experience, type, location }) {
  return (
    <div className="relative bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between overflow-hidden hover:shadow-md transition-shadow group select-none min-h-[220px]">
      
      {/* Top Right Corner Background Wave Graphic */}
      <img
        src={bgCorner}
        alt="Card corner decoration"
        className="absolute top-0 right-0 w-[130px] sm:w-[140px] md:w-[115px] lg:w-[130px] xl:w-[145px] h-auto pointer-events-none select-none z-0 object-contain object-right-top"
      />

      <div className="relative z-10">
        {/* Job Title & Department */}
        <div className="text-left mb-4 pr-16">
          <h3 className="text-base sm:text-lg font-bold text-[#3562D6] leading-snug group-hover:text-[#2563EB] transition-colors">
            {title}
          </h3>
          <p className="text-xs sm:text-sm font-medium text-slate-500 mt-0.5">{department}</p>
        </div>

        {/* Metadata Details */}
        <div className="space-y-2.5 text-xs sm:text-sm text-slate-600 font-semibold mb-6">
          {/* Row 1: Experience & Job Type side by side */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-500 shrink-0" />
              <span>{experience}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Briefcase className="w-4 h-4 text-[#C026D3] shrink-0" />
              <span>{type}</span>
            </div>
          </div>

          {/* Row 2: Location */}
          <div className="flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-red-500 shrink-0" />
            <span>{location}</span>
          </div>
        </div>
      </div>

      {/* Apply Now Action Button */}
      <button 
        type="button" 
        className="relative z-10 w-full py-3 bg-[#8CC63F] hover:bg-[#7db535] active:scale-[0.99] text-white font-bold text-sm tracking-wide rounded-2xl shadow-sm transition-all duration-200 cursor-pointer"
      >
        Apply Now
      </button>

    </div>
  );
}

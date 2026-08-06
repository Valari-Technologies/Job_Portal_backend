import React from 'react';
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="relative z-30 w-full flex justify-between items-center pointer-events-auto">
      {/* Brand Logo & Tagline */}
      <Link to="/login" className="flex items-center gap-2 sm:gap-3 md:gap-3.5 cursor-pointer text-left focus:outline-none">
        <div className="w-9 h-9 sm:w-12 sm:h-12 md:w-[54px] md:h-[54px] rounded-xl sm:rounded-2xl bg-[#84A43C] text-white flex items-center justify-center shadow-lg shadow-[#84A43C]/25 shrink-0 hover:bg-[#73922f] transition-all">
          <svg className="w-4 h-4 sm:w-6 sm:h-6 md:w-7 md:h-7 fill-current" viewBox="0 0 24 24">
            <path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/>
          </svg>
        </div>
        <div className="flex flex-col justify-center">
          <div className="flex items-center gap-1 sm:gap-1.5 text-lg sm:text-2xl md:text-[28px] font-black tracking-tight leading-none">
            <span className="text-[#3a3a3a]">TN</span>
            <span className="text-[#E29D29]">JOBZ</span>
          </div>
          <span className="text-[7.5px] sm:text-xs md:text-xs font-bold text-[#8E9B90] tracking-wider uppercase mt-0.5 sm:mt-1 whitespace-nowrap">
            FIND JOBS. BUILD CAREERS.
          </span>
        </div>
      </Link>

      {/* Top Right Auth Nav */}
      <div className="flex items-center gap-1.5 sm:gap-4 text-xs sm:text-base md:text-lg font-bold tracking-wide shrink-0 whitespace-nowrap">
        <Link to="/login" className="text-[#212B36] transition-colors cursor-pointer p-0.5 sm:p-1">
          Sign In
        </Link>
        <span className="text-[#D0D7D1]">|</span>
        <Link to="/register" className="text-[#FF6A55] hover:text-[#e05642] transition-colors cursor-pointer p-0.5 sm:p-1">
          Sign Up
        </Link>
      </div>
    </header>
  );
}

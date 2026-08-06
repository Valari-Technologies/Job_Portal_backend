import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="w-full max-w-[440px] mx-auto md:mx-0 p-2 sm:p-4 md:p-0 md:bg-transparent rounded-3xl md:rounded-none">
      {/* Welcome Headings */}
      <div className="mb-6 sm:mb-8">
        <p className="text-[#2D3748] text-xl sm:text-2xl md:text-2xl font-medium tracking-tight mb-1">
          Hello there,
        </p>
        <h1 className="text-3xl sm:text-4xl md:text-[42px] font-black text-[#1A202C] tracking-tight leading-tight">
          Welcome to <span className="text-[#84A43C]">TN Jobz</span>
        </h1>
      </div>

      <form onSubmit={(e) => e.preventDefault()} className="space-y-5 sm:space-y-6 flex flex-col items-center">
        {/* EMAIL FIELD */}
        <div className="w-full">
          <label className="block text-xs sm:text-xs md:text-sm font-bold text-[#64748B] tracking-wider uppercase mb-2">
            EMAIL
          </label>
          <div className="relative flex items-center">
            <Mail className="absolute left-4 w-4 h-4 sm:w-5 sm:h-5 text-[#94A3B8]" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              className="w-full pl-11 sm:pl-12 pr-4 py-3 sm:py-3.5 bg-white border border-[#E2E8F0] rounded-2xl text-sm sm:text-base font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
            />
          </div>
        </div>

        {/* PASSWORD FIELD */}
        <div className="w-full">
          <label className="block text-xs sm:text-xs md:text-sm font-bold text-[#64748B] tracking-wider uppercase mb-2">
            PASSWORD
          </label>
          <div className="relative flex items-center">
            <Lock className="absolute left-4 w-4 h-4 sm:w-5 sm:h-5 text-[#94A3B8]" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full pl-11 sm:pl-12 pr-11 sm:pr-12 py-3 sm:py-3.5 bg-white border border-[#E2E8F0] rounded-2xl text-sm sm:text-base font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 text-[#94A3B8] hover:text-[#64748B] transition-colors cursor-pointer"
            >
              {showPassword ? <EyeOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
            </button>
          </div>
        </div>

        {/* FORGOT PASSWORD */}
        <div className="w-full flex justify-end pt-0.5">
          <a href="#forgot" className="text-xs sm:text-xs md:text-sm font-bold text-[#FF6A55] hover:underline cursor-pointer">
            Forgot password?
          </a>
        </div>

        {/* LOGIN BUTTON - Centered relative to the form width */}
        <div className="flex justify-center w-full pt-1">
          <button
            type="submit"
            className="w-[220px] sm:w-[260px] md:w-[260px] py-3.5 sm:py-4 bg-[#84A43C] hover:bg-[#73922f] active:scale-[0.99] text-white font-bold text-sm sm:text-base md:text-lg tracking-wider rounded-2xl shadow-lg shadow-[#84A43C]/30 transition-all duration-200 uppercase cursor-pointer"
          >
            LOGIN
          </button>
        </div>
      </form>
    </div>
  );
}

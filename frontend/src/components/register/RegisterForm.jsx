import React, { useState } from 'react';
import { User, Mail, Phone, Lock, Eye, EyeOff, UserPlus } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import LegalModal from './LegalModal';

export default function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [error, setError] = useState('');

  // Modal State Management
  const [isLegalModalOpen, setIsLegalModalOpen] = useState(false);
  const [termsReviewed, setTermsReviewed] = useState(false);
  const [privacyReviewed, setPrivacyReviewed] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!termsReviewed || !privacyReviewed) {
      setError('Please review both Terms & Conditions and Privacy Policy before continuing.');
      return;
    }

    if (!agreeToTerms) {
      setError('You must accept the Terms & Conditions and Privacy Policy to continue.');
      return;
    }

    setError('');
    const isHr = email.toLowerCase().includes('hr');
    if (isHr) {
      const authData = { fullName, email, password };
      localStorage.setItem('hrAuth', JSON.stringify(authData));
      localStorage.removeItem('hrProfile'); // force profile refresh
      alert('HR Account created successfully!');
    } else {
      const authData = { fullName, email, password };
      localStorage.setItem('candidateAuth', JSON.stringify(authData));
      localStorage.removeItem('candidateProfile'); // force profile refresh
      alert('Candidate Account created successfully!');
    }
    navigate('/login');
  };

  const isFormValid = termsReviewed && privacyReviewed && agreeToTerms;

  return (
    <div className="w-full max-w-[680px] mx-auto bg-white/90 md:bg-transparent backdrop-blur-md md:backdrop-blur-none p-6 sm:p-8 md:p-0 rounded-3xl shadow-xl md:shadow-none border border-white/60 md:border-none">
      {/* Title Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-[36px] font-black text-[#84A43C] tracking-tight leading-tight mb-2">
          Create Account
        </h1>
        <p className="text-[#8E9B90] text-sm font-medium">
          Fill in the details below to get started
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Row 1: Full Name & Email Address */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs md:text-sm font-bold text-[#64748B] tracking-wider mb-2">
              Full Name
            </label>
            <div className="relative flex items-center">
              <User className="absolute left-4 w-4.5 h-4.5 text-[#94A3B8]" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs md:text-sm font-bold text-[#64748B] tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative flex items-center">
              <Mail className="absolute left-4 w-4.5 h-4.5 text-[#94A3B8]" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
              />
            </div>
          </div>
        </div>

        {/* Row 2: Phone Number & Password */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs md:text-sm font-bold text-[#64748B] tracking-wider mb-2">
              Phone Number
            </label>
            <div className="relative flex items-center">
              <Phone className="absolute left-4 w-4.5 h-4.5 text-[#94A3B8]" />
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="Enter your phone number"
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs md:text-sm font-bold text-[#64748B] tracking-wider mb-2">
              Password
            </label>
            <div className="relative flex items-center">
              <Lock className="absolute left-4 w-4.5 h-4.5 text-[#94A3B8]" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password"
                className="w-full pl-11 pr-11 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 text-[#94A3B8] hover:text-[#64748B] transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Row 3: Confirm Password */}
        <div>
          <label className="block text-xs md:text-sm font-bold text-[#64748B] tracking-wider mb-2">
            Confirm Password
          </label>
          <div className="relative flex items-center">
            <Lock className="absolute left-4 w-4.5 h-4.5 text-[#94A3B8]" />
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              className="w-full pl-11 pr-11 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-4 text-[#94A3B8] hover:text-[#64748B] transition-colors cursor-pointer"
            >
              {showConfirmPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
            </button>
          </div>
        </div>

        {/* Terms and Conditions Checkbox Area */}
        <div className="flex flex-col gap-1.5 pt-1 select-none">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="terms"
              checked={agreeToTerms}
              disabled={!(termsReviewed && privacyReviewed)}
              onChange={(e) => {
                setAgreeToTerms(e.target.checked);
                if (e.target.checked) setError('');
              }}
              className={`w-4 h-4 rounded-sm focus:ring-[#84A43C]/30 ${
                (termsReviewed && privacyReviewed)
                  ? 'text-[#84A43C] border-[#E2E8F0] cursor-pointer'
                  : 'text-gray-300 border-gray-200 cursor-not-allowed opacity-50'
              }`}
              aria-describedby={error ? "terms-error" : undefined}
            />
            <label htmlFor="terms" className="text-xs md:text-sm font-medium text-[#64748B]">
              I agree to the{' '}
              <button
                type="button"
                onClick={() => setIsLegalModalOpen(true)}
                className="text-[#84A43C] font-semibold hover:underline cursor-pointer focus:outline-none"
              >
                Terms & Conditions
              </button>{' '}
              and{' '}
              <button
                type="button"
                onClick={() => setIsLegalModalOpen(true)}
                className="text-[#84A43C] font-semibold hover:underline cursor-pointer focus:outline-none"
              >
                Privacy Policy
              </button>
            </label>
          </div>

          {/* Helper Message if legal agreements aren't reviewed yet */}
          {!(termsReviewed && privacyReviewed) && (
            <p className="text-xs text-amber-600 font-semibold mt-1">
              Please review both Terms & Conditions and Privacy Policy before continuing.
            </p>
          )}

          {/* Inline Validation Error Messages */}
          {error && (
            <p id="terms-error" className="text-xs font-bold text-red-500 mt-1" role="alert">
              {error}
            </p>
          )}
        </div>

        {/* Buttons Action Area */}
        <div className="pt-3">
          {/* CREATE ACCOUNT BUTTON */}
          <button
            type="submit"
            className={`flex items-center justify-center gap-2 w-full py-3.5 font-bold text-sm md:text-base tracking-wider rounded-2xl shadow-lg transition-all duration-200 cursor-pointer ${
              isFormValid
                ? 'bg-[#84A43C] hover:bg-[#73922f] active:scale-[0.99] text-white shadow-[#84A43C]/30'
                : 'bg-gray-300 text-gray-500 opacity-60'
            }`}
          >
            <UserPlus className="w-5 h-5" />
            <span>Create Account</span>
          </button>
        </div>

        {/* Navigation Link to Login */}
        <div className="text-center pt-4">
          <p className="text-xs md:text-sm text-[#64748B] font-medium">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-[#84A43C] font-bold hover:underline cursor-pointer"
            >
              Login
            </Link>
          </p>
        </div>
      </form>

      {/* Combined Single Legal Agreements Modal */}
      <LegalModal
        isOpen={isLegalModalOpen}
        onClose={() => setIsLegalModalOpen(false)}
        termsReviewed={termsReviewed}
        setTermsReviewed={setTermsReviewed}
        privacyReviewed={privacyReviewed}
        setPrivacyReviewed={setPrivacyReviewed}
      />
    </div>
  );
}

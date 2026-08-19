import React, { useState } from 'react';
import { User, Mail, Phone, Lock, Eye, EyeOff, UserPlus } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
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

  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // Modal State Management
  const [isLegalModalOpen, setIsLegalModalOpen] = useState(false);
  const [termsReviewed, setTermsReviewed] = useState(false);
  const [privacyReviewed, setPrivacyReviewed] = useState(false);
  const navigate = useNavigate();

  const firstMessage = (value) => (Array.isArray(value) ? value[0] : value);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFieldErrors({});
    setError('');
    setSuccess('');

    if (!termsReviewed || !privacyReviewed) {
      setError('Please review both Terms & Conditions and Privacy Policy before continuing.');
      return;
    }

    if (!agreeToTerms) {
      setError('You must accept the Terms & Conditions and Privacy Policy to continue.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      const isHr = email.toLowerCase().includes('hr');
      let response;
      if (isHr) {
        // Map frontend fields to backend HR fields
        const names = fullName.split(' ', 1);
        const firstName = names[0] || '';
        const lastName = fullName.substring(firstName.length).trim() || '';
        response = await axios.post('http://127.0.0.1:8000/accounts/register/hr/', {
          username: email,
          email: email,
          password: password,
          first_name: firstName,
          last_name: lastName,
          phone_number: phoneNumber
        });
      } else {
        response = await axios.post('http://127.0.0.1:8000/accounts/register/candidate/', {
          fullName,
          email,
          phoneNumber,
          password,
          confirmPassword,
          agreeToTerms
        });
      }

      setSuccess('Account created successfully! Redirecting to login...');
      setFullName('');
      setEmail('');
      setPhoneNumber('');
      setPassword('');
      setConfirmPassword('');
      setAgreeToTerms(false);

      setTimeout(() => navigate('/login'), 1500);

    } catch (err) {
      if (err.response && err.response.data) {
        const data = err.response.data;
        if (data.detail) {
          setError(firstMessage(data.detail));
        } else if (typeof data === 'object') {
          setFieldErrors(data);
          if (data.non_field_errors) {
            setError(firstMessage(data.non_field_errors));
          } else {
            // Find first field error to show in main alert banner
            const keys = Object.keys(data);
            if (keys.length > 0) {
              const firstKey = keys[0];
              setError(`${firstKey}: ${firstMessage(data[firstKey])}`);
            }
          }
        } else {
          setError('Registration failed. Please check the details and try again.');
        }
      } else {
        setError('Failed to connect to backend server.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fieldError = (name) =>
    fieldErrors[name] ? (
      <p className="mt-1.5 text-xs font-semibold text-red-600">
        {firstMessage(fieldErrors[name])}
      </p>
    ) : null;

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

      {/* ERROR MESSAGE ALERT */}
      {error && (
        <div className="mb-5 p-4 bg-red-50 border border-red-200 text-red-700 text-sm font-semibold rounded-2xl w-full text-center">
          {error}
        </div>
      )}

      {/* SUCCESS MESSAGE ALERT */}
      {success && (
        <div className="mb-5 p-4 bg-green-50 border border-green-200 text-green-700 text-sm font-semibold rounded-2xl w-full text-center">
          {success}
        </div>
      )}

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
                disabled={loading}
                required
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs disabled:opacity-75"
              />
            </div>
            {fieldError('fullName')}
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
                disabled={loading}
                required
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs disabled:opacity-75"
              />
            </div>
            {fieldError('email')}
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
                disabled={loading}
                required
                className="w-full pl-11 pr-4 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs disabled:opacity-75"
              />
            </div>
            {fieldError('phoneNumber')}
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
                disabled={loading}
                required
                className="w-full pl-11 pr-11 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs disabled:opacity-75"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 text-[#94A3B8] hover:text-[#64748B] transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
              </button>
            </div>
            {fieldError('password')}
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
              disabled={loading}
              required
              className="w-full pl-11 pr-11 py-3 bg-white border border-[#E2E8F0] rounded-2xl text-sm font-medium text-[#1E293B] placeholder-[#94A3B8] outline-none focus:border-[#84A43C] focus:ring-4 focus:ring-[#84A43C]/15 transition-all shadow-xs disabled:opacity-75"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-4 text-[#94A3B8] hover:text-[#64748B] transition-colors cursor-pointer"
            >
              {showConfirmPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
            </button>
          </div>
          {fieldError('confirmPassword')}
        </div>

        {/* Terms and Conditions Checkbox Area */}
        <div className="flex flex-col gap-1.5 pt-1 select-none">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="terms"
              checked={agreeToTerms}
              disabled={!(termsReviewed && privacyReviewed) || loading}
              onChange={(e) => {
                setAgreeToTerms(e.target.checked);
                if (e.target.checked) setError('');
              }}
              className={`w-4 h-4 rounded-sm focus:ring-[#84A43C]/30 ${
                (termsReviewed && privacyReviewed && !loading)
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
        {fieldError('agreeToTerms')}

        {/* Buttons Action Area */}
        <div className="pt-3">
          {/* CREATE ACCOUNT BUTTON */}
          <button
            type="submit"
            disabled={loading || !isFormValid}
            className={`flex items-center justify-center gap-2 w-full py-3.5 font-bold text-sm md:text-base tracking-wider rounded-2xl shadow-lg transition-all duration-200 cursor-pointer ${
              (isFormValid && !loading)
                ? 'bg-[#84A43C] hover:bg-[#73922f] active:scale-[0.99] text-white shadow-[#84A43C]/30'
                : 'bg-gray-300 text-gray-500 opacity-60 cursor-not-allowed'
            }`}
          >
            <UserPlus className="w-5 h-5" />
            <span>{loading ? 'Creating Account...' : 'Create Account'}</span>
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

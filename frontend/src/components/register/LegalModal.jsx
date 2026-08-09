import React, { useState, useRef, useEffect } from 'react';
import { X, FileText, Shield, CheckCircle2 } from 'lucide-react';

export default function LegalModal({ 
  isOpen, 
  onClose, 
  termsReviewed, 
  setTermsReviewed, 
  privacyReviewed, 
  setPrivacyReviewed 
}) {
  const [activeTab, setActiveTab] = useState('terms'); // 'terms' | 'privacy'
  const scrollContainerRef = useRef(null);

  // Reset scroll position when switching tabs
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [activeTab, isOpen]);

  if (!isOpen) return null;

  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container) return;

    // Check if user scrolled to the bottom (within a 10px threshold)
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 10;
    
    if (isAtBottom) {
      if (activeTab === 'terms' && !termsReviewed) {
        setTermsReviewed(true);
      } else if (activeTab === 'privacy' && !privacyReviewed) {
        setPrivacyReviewed(true);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Dark Blurred Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Centered Modal Container */}
      <div className="relative bg-white rounded-3xl w-full max-w-2xl h-[80vh] flex flex-col shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#84A43C]/10 text-[#84A43C] flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Legal Agreement Review</h2>
              <p className="text-[11px] text-slate-400 font-medium">Please review both documents to proceed</p>
            </div>
          </div>
          <button 
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-lg hover:bg-slate-100 cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection Bar */}
        <div className="flex border-b border-slate-100 bg-slate-50/30 p-2 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('terms')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs sm:text-sm font-bold rounded-xl transition-all cursor-pointer ${
              activeTab === 'terms'
                ? 'bg-white text-[#84A43C] shadow-xs border border-slate-100'
                : 'text-slate-500 hover:text-slate-800 hover:bg-white/50'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>1. Terms & Conditions</span>
            {termsReviewed && <CheckCircle2 className="w-4 h-4 text-[#84A43C] fill-[#84A43C]/10" />}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('privacy')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs sm:text-sm font-bold rounded-xl transition-all cursor-pointer ${
              activeTab === 'privacy'
                ? 'bg-white text-[#84A43C] shadow-xs border border-slate-100'
                : 'text-slate-500 hover:text-slate-800 hover:bg-white/50'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>2. Privacy Policy</span>
            {privacyReviewed && <CheckCircle2 className="w-4 h-4 text-[#84A43C] fill-[#84A43C]/10" />}
          </button>
        </div>

        {/* Modal Body (Scrollable Tab Content) */}
        <div 
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="p-6 md:p-8 overflow-y-auto flex-grow space-y-6 text-sm sm:text-base leading-relaxed text-slate-600"
        >
          {activeTab === 'terms' ? (
            <>
              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">1. Agreement to Terms</h3>
                <p>
                  By accessing or using the <strong>TN Jobz</strong> <strong>job portal</strong>, creating a <strong>candidate profile</strong>, or submitting a <strong>job application</strong>, you agree to be bound by this legal agreement. If you do not accept these terms in full, you must not access or register on our <strong>hiring platform</strong>.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">2. Eligibility</h3>
                <p>
                  You must be at least 18 years of age or the age of legal majority in your jurisdiction to register an account and seek <strong>career opportunities</strong> or post <strong>employment opportunities</strong> on TN Jobz. By signing up, you verify that your registration details are accurate.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">3. Resume Upload & Profile Accuracy</h3>
                <p>
                  Our <strong>hiring platform</strong> permits <strong>resume upload</strong> and text-based details. You warrant that all credentials, certificates, and job histories listed in your <strong>candidate profile</strong> represent true statements. TN Jobz reserves the right to suspend any account presenting counterfeit information.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">4. Recruiter Interactions</h3>
                <p>
                  Prospective employers and registered <strong>recruiter</strong> accounts can view candidate files. While we mandate professional behavior, TN Jobz is not responsible for negotiations, background checks, or employment contracts offered outside the platform.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">5. Prohibited Activities</h3>
                <p>
                  Users are strictly forbidden from scraping job listings, sending bulk spam messages, uploading files with malicious software, or using automated scripts to apply for listings. Breach of this clause will lead to permanent account suspension.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">6. Limitation of Liability</h3>
                <p>
                  We provide the platform "as is" without guarantees of success. TN Jobz is not liable for errors in listings, communication delays, or any direct/indirect damages arising from job application failures.
                </p>
              </section>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-xs">
                <p className="font-bold text-slate-700 mb-1">Status:</p>
                {termsReviewed ? (
                  <span className="text-[#84A43C] font-bold flex items-center gap-1">
                    ✓ You have successfully reviewed the Terms & Conditions.
                  </span>
                ) : (
                  <span className="text-amber-600 font-bold">
                    🛈 Please scroll down to the bottom to finish reviewing the Terms & Conditions.
                  </span>
                )}
              </div>
            </>
          ) : (
            <>
              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">1. Data Collection</h3>
                <p>
                  We collect credentials, details of your <strong>candidate profile</strong>, phone details, and document metadata provided during <strong>resume upload</strong>. This information lets us deliver relevant <strong>career opportunities</strong>.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">2. How We Use Data</h3>
                <p>
                  We process data to recommend <strong>employment opportunities</strong>, transmit a <strong>job application</strong> to a prospective <strong>recruiter</strong>, enhance search algorithms, and block profile impersonation.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">3. Cookies and Analytics</h3>
                <p>
                  Cookies track user settings and sessions to maintain a high-quality user experience. Disabling cookies in settings may restrict some system features on the <strong>hiring platform</strong>.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">4. Third-Party Sharing</h3>
                <p>
                  We share candidate profiles with registered recruiter accounts only when you apply. We do not sell user data to secondary advertisers or databases.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">5. Data Security</h3>
                <p>
                  We prioritize <strong>privacy protection</strong> and apply strict <strong>data security</strong> measures, including encryption (SSL) and secure access controls, to safeguard candidate credentials.
                </p>
              </section>

              <section>
                <h3 className="text-base font-bold text-slate-800 mb-2">6. User Rights & Data Deletion</h3>
                <p>
                  You can access, modify, or permanently delete your account data inside your profile settings page. Deletion request processes occur within 30 days of submission.
                </p>
              </section>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100 text-xs">
                <p className="font-bold text-slate-700 mb-1">Status:</p>
                {privacyReviewed ? (
                  <span className="text-[#84A43C] font-bold flex items-center gap-1">
                    ✓ You have successfully reviewed the Privacy Policy.
                  </span>
                ) : (
                  <span className="text-amber-600 font-bold">
                    🛈 Please scroll down to the bottom to finish reviewing the Privacy Policy.
                  </span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <div className="text-xs font-semibold flex flex-col gap-0.5 text-slate-500">
            <div>Terms: <span className={termsReviewed ? 'text-[#84A43C]' : 'text-amber-500'}>{termsReviewed ? 'Reviewed' : 'Pending'}</span></div>
            <div>Privacy: <span className={privacyReviewed ? 'text-[#84A43C]' : 'text-amber-500'}>{privacyReviewed ? 'Reviewed' : 'Pending'}</span></div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-sm font-bold text-white bg-[#84A43C] hover:bg-[#73922f] rounded-xl shadow-xs transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}

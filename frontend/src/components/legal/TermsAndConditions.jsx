import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, FileText } from 'lucide-react';

export default function TermsAndConditions() {
  return (
    <div className="min-h-screen bg-slate-50 text-[#1E293B] font-sans flex flex-col justify-between">
      {/* Header */}
      <header className="bg-white border-b border-[#E2E8F0] py-4 px-6 md:px-12 flex justify-between items-center shadow-xs">
        <Link to="/register" className="flex items-center gap-2 text-[#84A43C] font-semibold hover:underline">
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Register</span>
        </Link>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#84A43C] text-white flex items-center justify-center">
            <FileText className="w-4.5 h-4.5" />
          </div>
          <span className="text-lg font-black text-[#3a3a3a]">TN <span className="text-[#E29D29]">JOBZ</span></span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl w-full mx-auto px-6 py-10 md:py-16 flex-grow">
        <div className="bg-white rounded-3xl p-6 sm:p-10 md:p-12 shadow-sm border border-[#E2E8F0]">
          
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-[#84A43C]/10 text-[#84A43C] flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-[#1A202C]">Terms & Conditions</h1>
              <p className="text-sm text-[#8E9B90]">Last Updated: August 6, 2026</p>
            </div>
          </div>

          <div className="space-y-8 text-sm sm:text-base leading-relaxed text-[#4A5568]">
            
            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">1. Introduction and Agreement</h2>
              <p>
                Welcome to <strong>TN Jobz</strong>, a premium <strong>hiring platform</strong> and <strong>job portal</strong> designed to connect talent with stellar <strong>career opportunities</strong>. By accessing our website, creating a <strong>candidate profile</strong>, or utilizing our services for submitting a <strong>job application</strong>, you agree to be bound by these Terms & Conditions. If you do not agree to these terms, please do not use our services.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">2. Eligibility</h2>
              <p>
                To register an account or search for <strong>employment opportunities</strong> on TN Jobz, you must be at least 18 years of age (or the age of majority in your jurisdiction) and possess the legal authority to enter into these terms. By using our <strong>job portal</strong>, you warrant that all information provided during registration is accurate and truthful.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">3. Account Registration and Security</h2>
              <p>
                When you create an account, you must choose a secure password. You are solely responsible for maintaining the confidentiality of your credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized access.
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>Provide accurate, current, and complete registration details.</li>
                <li>Do not share login credentials or transfer accounts.</li>
                <li>Maintain and promptly update your <strong>candidate profile</strong> to keep it accurate.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">4. Resume and Profile Information</h2>
              <p>
                Our services include features facilitating <strong>resume upload</strong> and the configuration of detailed job profiles. You retain ownership of the content you upload; however, by posting it, you grant TN Jobz a worldwide, non-exclusive license to display, index, and share this information with verified employers.
              </p>
              <p className="mt-2">
                We prioritize <strong>privacy protection</strong> and implement strict <strong>data security</strong> measures, but you are responsible for ensuring your uploaded files do not contain malicious code, copyright-infringing material, or false biographical details.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">5. Job Applications</h2>
              <p>
                When you submit a <strong>job application</strong> through our <strong>hiring platform</strong>, your resume, contact details, and custom answers are transmitted directly to the prospective employer or <strong>recruiter</strong>. While we verify job listings, TN Jobz does not guarantee the validity of any job offer or the outcome of any application process.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">6. Recruiter Interactions</h2>
              <p>
                As a candidate, you may receive communication directly from a registered <strong>recruiter</strong> or employer. TN Jobz acts as a facilitator and is not responsible for the nature, content, or safety of agreements, interviews, or hiring negotiations conducted outside our official platform interfaces.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">7. User Responsibilities</h2>
              <p>
                Users must act professionally and respectfully in all interactions. You represent and warrant that you will use our services in compliance with local employment laws, non-discrimination regulations, and privacy standards.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">8. Prohibited Activities</h2>
              <p>
                You agree not to engage in any of the following activities on our platform:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1.5">
                <li>Uploading fraudulent resumes or misrepresenting qualifications.</li>
                <li>Scraping job listings, candidate information, or database content without written permission.</li>
                <li>Posting spam, unsolicited promotional messages, or duplicate listings.</li>
                <li>Attempting to bypass our authentication protocols or test our platform vulnerabilities.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">9. Termination</h2>
              <p>
                We reserve the right to suspend or terminate your access to TN Jobz at our sole discretion, without notice, if we believe you have breached these Terms or engaged in behavior detrimental to other candidates, recruiters, or the platform integrity.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">10. Contact Information</h2>
              <p>
                If you have any questions regarding these Terms & Conditions, please contact us at:
              </p>
              <p className="mt-2 text-sm font-semibold text-[#84A43C]">
                Email: support@tnjobz.com<br />
                Address: TN Jobz Legal Dept, Chennai, Tamil Nadu, India
              </p>
            </section>

          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-[#E2E8F0] py-6 text-center text-xs text-[#8E9B90]">
        &copy; {new Date().getFullYear()} TN Jobz. All rights reserved.
      </footer>
    </div>
  );
}

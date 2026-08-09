import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, Shield } from 'lucide-react';

export default function PrivacyPolicy() {
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
            <Shield className="w-4.5 h-4.5" />
          </div>
          <span className="text-lg font-black text-[#3a3a3a]">TN <span className="text-[#E29D29]">JOBZ</span></span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl w-full mx-auto px-6 py-10 md:py-16 flex-grow">
        <div className="bg-white rounded-3xl p-6 sm:p-10 md:p-12 shadow-sm border border-[#E2E8F0]">
          
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-[#84A43C]/10 text-[#84A43C] flex items-center justify-center">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-[#1A202C]">Privacy Policy</h1>
              <p className="text-sm text-[#8E9B90]">Last Updated: August 6, 2026</p>
            </div>
          </div>

          <div className="space-y-8 text-sm sm:text-base leading-relaxed text-[#4A5568]">
            
            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">1. Introduction</h2>
              <p>
                At <strong>TN Jobz</strong>, we are committed to safeguarding the privacy of our candidates, recruiters, and website users. This Privacy Policy details how we collect, process, share, and protect your personal information on our <strong>hiring platform</strong>. Our pledge of <strong>privacy protection</strong> ensures that your journey toward fresh <strong>career opportunities</strong> remains safe and secure.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">2. Data Collection</h2>
              <p>
                We collect information necessary to deliver our recruitment matching services. This information includes:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1.5">
                <li><strong>Account Registration Details</strong>: Full Name, email address, phone number, and password.</li>
                <li><strong>Candidate Profile</strong> Data: Employment history, educational records, skills, photos, and preferred locations.</li>
                <li><strong>Resume Files</strong>: Information extracted from your document via <strong>resume upload</strong>.</li>
                <li><strong>Application Activity</strong>: Details regarding any <strong>job application</strong> you submit, including cover letters.</li>
                <li><strong>Technical Data</strong>: IP address, browser type, cookies, and system identifier details.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">3. Data Usage</h2>
              <p>
                We process your personal information for the following specific purposes:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1.5">
                <li>Facilitating access to <strong>employment opportunities</strong> on our <strong>job portal</strong>.</li>
                <li>Transmitting applications and candidate details directly to the relevant employer or <strong>recruiter</strong>.</li>
                <li>Improving our system matching algorithms, visual layout, and user experience.</li>
                <li>Verifying recruiter registrations to prevent fraudulent job postings.</li>
                <li>Communicating critical updates, account status notifications, or newsletter content.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">4. Cookies</h2>
              <p>
                We use tracking cookies, local storage tokens, and analytics snippets to recognize you upon returning, remember your preferences, and track aggregate user traffic patterns. You can manage or disable cookies through your personal browser settings, although doing so might impact some features of our platform.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">5. Data Security</h2>
              <p>
                We prioritize high-grade <strong>data security</strong>. TN Jobz employs industry-standard encryption protocols (SSL/TLS), secure database firewalls, and credential access limitations to ensure the safety of your information. While we implement robust safeguards, no method of transmission over the internet can be guaranteed as 100% secure.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">6. Third-Party Services</h2>
              <p>
                We do not sell, rent, or trade your candidate details. However, we share information with verified recruiters, cloud hosting infrastructure vendors, payment gateways, and authentication providers (e.g., Google Sign-In) to carry out core system functions. All third-party partners are contracted to handle your data securely.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">7. User Rights</h2>
              <p>
                You retain complete control over your data. Under local and international data protection laws, you possess the right to:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>Access and export the personal data associated with your profile.</li>
                <li>Correct or update inaccurate information in your account settings.</li>
                <li>Request the permanent deletion of your profile and data from our systems.</li>
                <li>Withdraw consent to promotional emails or profiling.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-[#1A202C] mb-3">8. Contact Information</h2>
              <p>
                If you have questions, feedback, or data deletion requests, contact our Privacy Officer at:
              </p>
              <p className="mt-2 text-sm font-semibold text-[#84A43C]">
                Email: privacy@tnjobz.com<br />
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

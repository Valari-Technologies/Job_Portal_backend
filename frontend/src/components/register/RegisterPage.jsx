import React from 'react';
import RegisterForm from './RegisterForm';
import bgImage from '../../assets/register/register-bg.png';

export default function RegisterPage() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#FAFAFA] font-sans flex flex-col justify-between">
      {/* Background Graphic Image - Hidden on mobile, visible on desktop/tablet */}
      <img
        src={bgImage}
        alt="TN Jobz Background"
        className="hidden md:block absolute inset-0 w-full h-full object-cover object-center z-0 select-none pointer-events-none"
      />

      {/* Main Container - Responsive layout with clean mobile, tablet, and desktop spacing */}
      <div className="relative z-10 w-full min-h-screen flex flex-col justify-between p-4 sm:p-8 lg:p-10">
        {/* Dynamic Form Container */}
        <main className="w-full max-w-7xl mx-auto my-auto pt-6 sm:pt-8 md:pt-28 lg:pt-32 xl:pt-4 md:mt-0 xl:-mt-6 md:pl-20 lg:pl-44 xl:pl-56 flex items-center justify-center md:justify-start">
          <RegisterForm />
        </main>

        {/* Bottom space balance */}
        <div className="h-2 sm:h-4 w-full"></div>
      </div>
    </div>
  );
}

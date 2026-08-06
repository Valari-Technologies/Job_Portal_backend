import React from 'react';
import Header from './Header';
import LoginForm from './LoginForm';
import bgImage from '../../assets/login/tn-jobz-bg.jpg';

export default function LoginPage() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#FAFAFA] font-sans flex flex-col justify-between">
      {/* Background Graphic Image - Hidden on mobile, visible on desktop/tablet */}
      <img
        src={bgImage}
        alt="TN Jobz Background"
        className="hidden md:block absolute inset-0 w-full h-full object-cover object-center z-0 select-none pointer-events-none"
      />

      {/* Main Container - Responsive layout with clean mobile and desktop spacing */}
      <div className="relative z-10 w-full min-h-screen flex flex-col justify-between p-4 sm:p-8 lg:p-10">
        {/* Header Navigation */}
        <Header />

        {/* Form Container - Shifted slightly down (md:-mt-10) and rightward (md:pl-36 lg:pl-44 xl:pl-56) */}
        <main className="w-full max-w-7xl mx-auto my-auto pt-6 sm:pt-8 md:pt-4 md:pb-8 md:-mt-10 md:pl-36 lg:pl-44 xl:pl-56 flex items-center justify-center md:justify-start">
          <LoginForm />
        </main>

        {/* Bottom space balance */}
        <div className="h-2 sm:h-4 w-full"></div>
      </div>
    </div>
  );
}

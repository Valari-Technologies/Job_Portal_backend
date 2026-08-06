import React from 'react';
import Header from './components/Header';
import LoginForm from './components/LoginForm';
import bgImage from './assets/login/tn-jobz-bg.jpg';

export default function App() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#FAFAFA] font-sans flex flex-col justify-between">
      {/* Background Graphic Image - Hidden on mobile, visible on desktop/tablet */}
      <img
        src={bgImage}
        alt="TN Jobz Background"
        className="hidden md:block absolute inset-0 w-full h-full object-cover object-center z-0 select-none pointer-events-none"
      />

      {/* Main Container - Responsive layout with clean mobile and desktop spacing */}
      <div className="relative z-10 w-full min-h-screen flex flex-col justify-between p-3 sm:p-8 lg:p-10">
        {/* Header Navigation */}
        <Header />

        {/* Form Container - Smoothly positioned slightly lower on desktop/mobile to fit inside white background area */}
        <main className="w-full max-w-7xl mx-auto my-auto pt-4 sm:pt-8 md:pt-4 md:pb-12 md:mt-2 md:pl-24 lg:pl-36 xl:pl-48 flex items-center justify-center md:justify-start">
          <LoginForm />
        </main>

        {/* Bottom space balance */}
        {/* <div className="h-2 sm:h-4 w-full"></div> */}
      </div>
    </div>
  );
}

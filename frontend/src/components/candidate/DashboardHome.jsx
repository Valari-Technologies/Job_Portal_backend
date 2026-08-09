import React from 'react';
import CandidateHeader from './CandidateHeader';
import StatCard from './StatCard';
import JobCard from './JobCard';
import ProfileCompletion from './ProfileCompletion';
import RecentApplications from './RecentApplications';
import QuickActions from './QuickActions';

export default function DashboardHome() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 px-2 sm:px-6 md:px-8 mt-4 flex-grow">
      {/* Left Columns (occupies 3 out of 4 grid spaces on large displays) */}
      <div className="xl:col-span-3 space-y-6 flex flex-col justify-between">
        
        {/* Header Greeting */}
        <CandidateHeader />

        {/* Stats Matrix Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            type="resume"
            title="Resume Status"
            value="Resume Uploaded"
            date="Updated on 15 May 2024"
          />
          <StatCard
            type="applications"
            title="You'"
            value="12"
            subtext="View all applications"
          />
          <StatCard
            type="opportunities"
            title="Current Opportunities"
            value="45"
            subtext="New jobs this week"
          />
        </div>

        {/* Job Recommendations Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between select-none">
            <h2 className="text-xl font-black text-[#E29D29] tracking-tight">Recommended / Latest Jobs</h2>
            <button type="button" className="text-xs font-bold text-[#2563EB] hover:underline cursor-pointer focus:outline-none">
              View All Jobs
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <JobCard
              title="UI/UX Designer"
              department="Design Team"
              experience="2-4 yrs"
              type="Full Time"
              location="Mumbai, India"
            />
            <JobCard
              title="Frontend Developer"
              department="Engineering"
              experience="3-5 yrs"
              type="Full Time"
              location="Bangalore, India"
            />
            <JobCard
              title="Product Manager"
              department="Product Team"
              experience="4-6 yrs"
              type="Full Time"
              location="Hyderabad, India"
            />
          </div>
        </div>

        {/* Recent Applications Listing Table */}
        <RecentApplications />

      </div>

      {/* Right Column (occupies 1 grid space) */}
      <div className="xl:col-span-1 space-y-6 flex flex-col justify-center">
        
        {/* Profile Completion Circle widget */}
        <ProfileCompletion />

        {/* Quick Actions Panel */}
        <QuickActions />

      </div>
    </div>
  );
}

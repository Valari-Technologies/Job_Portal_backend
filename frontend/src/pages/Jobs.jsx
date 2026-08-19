import React, { useState } from 'react';
import { Search, ChevronDown, Star, SlidersHorizontal, LayoutGrid, List, MapPin, Briefcase, Clock, Heart, CheckCircle2, Laptop, Server, Globe, ChevronLeft, ChevronRight } from 'lucide-react';
import bgCorner from '../assets/canditate/canditate-job-card-bgimage.png';

export default function Jobs() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSort, setSelectedSort] = useState('latest'); // 'latest' | 'relevance' | 'closing'
  const [viewType, setViewType] = useState('list'); // 'grid' | 'list'
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [savedJobs, setSavedJobs] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);

  // Sample job listings representing Figma design feed
  const jobListings = [
    { 
      id: 1, 
      title: 'UI/UX Designer', 
      company: 'Microsoft', 
      logoComponent: <Laptop className="w-7 h-7 text-slate-700" />,
      department: 'Design Department', 
      location: 'Bengaluru, Karnataka', 
      type: 'Full-time', 
      experience: '3-5 Yrs', 
      salary: '₹12-18 LPA', 
      posted: '2 days ago',
      skills: ['Figma', 'Adobe XD', 'UI Design', 'Prototyping'],
      extraSkills: 2
    },
    { 
      id: 2, 
      title: 'Frontend Developer', 
      company: 'Tata Consultancy Services', 
      logoComponent: <Server className="w-7 h-7 text-blue-600" />,
      department: 'Technology', 
      location: 'Hyderabad, Telangana', 
      type: 'Full-time', 
      experience: '2-4 Yrs', 
      salary: '₹6-10 LPA', 
      posted: '1 day ago',
      skills: ['React', 'JavaScript', 'TypeScript', 'CSS'],
      extraSkills: 1
    },
    { 
      id: 3, 
      title: 'Product Designer', 
      company: 'Infosys', 
      logoComponent: <Globe className="w-7 h-7 text-emerald-600" />,
      department: 'Product Team', 
      location: 'Pune, Maharashtra', 
      type: 'Full-time', 
      experience: '4-6 Yrs', 
      salary: '₹10-15 LPA', 
      posted: '5 days ago',
      skills: ['Figma', 'UI Design', 'User Research', 'Wireframing'],
      extraSkills: 2
    }
  ];

  const handleDropdownToggle = (name) => {
    setActiveDropdown(activeDropdown === name ? null : name);
  };

  const toggleSaveJob = (id) => {
    if (savedJobs.includes(id)) {
      setSavedJobs(savedJobs.filter(jobId => jobId !== id));
    } else {
      setSavedJobs([...savedJobs, id]);
    }
  };

  return (
    <div className="px-2 sm:px-6 md:px-8 mt-4 flex-grow space-y-6 animate-in fade-in duration-300 select-none text-left font-sans w-full">
      
      {/* Title Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[#84A43C] tracking-tight">Jobs</h1>
        <p className="text-sm font-semibold text-slate-400 mt-1">Explore and apply for the best opportunities</p>
      </div>

      {/* Row 1: Search, Save Search, Filter Button */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3 w-full">
        {/* Outlined Search Bar */}
        <div className="relative flex-grow flex items-center">
          <Search className="absolute left-4 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by job title, keyword or company"
            className="w-full pl-12 pr-4 py-3.5 bg-white border border-[#84A43C]/60 rounded-2xl text-sm font-medium text-slate-700 placeholder-slate-400 outline-none focus:border-[#84A43C] focus:ring-1 focus:ring-[#84A43C]/20 transition-all"
          />
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 shrink-0 w-full sm:w-auto flex-wrap sm:flex-nowrap">
          {/* Lime Green Search Button */}
          <button
            type="button"
            className="flex-grow sm:flex-grow-0 px-8 py-3.5 bg-[#84A43C] hover:bg-[#73922f] active:scale-[0.99] text-white font-bold text-sm rounded-2xl shadow-sm transition-all cursor-pointer text-center"
          >
            Search
          </button>

          {/* Save Search Button */}
          <button
            type="button"
            className="flex-grow sm:flex-grow-0 flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-slate-50 border border-slate-200 text-[#84A43C] font-bold text-sm rounded-2xl transition-colors cursor-pointer"
          >
            <Star className="w-4 h-4 text-[#84A43C]" />
            <span>Save Search</span>
          </button>

          {/* Toggle Filter Button */}
          <button
            type="button"
            className="p-3.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-500 rounded-2xl transition-colors cursor-pointer"
            aria-label="Filter panel"
          >
            <SlidersHorizontal className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Row 2: Dropdowns & Clear All */}
      <div className="flex items-center gap-3 flex-wrap">
        {[
          { label: 'Department', id: 'department' },
          { label: 'Location', id: 'location' },
          { label: 'Employment Type', id: 'employment' },
          { label: 'Experience Level', id: 'experience' },
          { label: 'Skills', id: 'skills' }
        ].map((drop) => (
          <div key={drop.id} className="relative">
            <button
              type="button"
              onClick={() => handleDropdownToggle(drop.id)}
              className="flex items-center justify-between gap-2 px-4 py-2.5 bg-white border border-[#84A43C]/40 hover:border-[#84A43C] rounded-2xl text-xs sm:text-sm font-semibold text-slate-600 transition-colors cursor-pointer focus:outline-none"
            >
              <span>{drop.label}</span>
              <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
            </button>
            {activeDropdown === drop.id && (
              <div className="absolute left-0 mt-2 w-48 bg-white border border-slate-100 rounded-2xl shadow-lg z-30 p-2 py-3 animate-in fade-in slide-in-from-top-2 duration-150">
                <p className="text-xs text-slate-400 px-3 pb-1.5 font-bold uppercase tracking-wider">Select {drop.label}</p>
                <button type="button" className="w-full text-left px-3 py-2 text-sm text-slate-600 font-semibold hover:bg-slate-50 rounded-xl">Option 1</button>
                <button type="button" className="w-full text-left px-3 py-2 text-sm text-slate-600 font-semibold hover:bg-slate-50 rounded-xl">Option 2</button>
              </div>
            )}
          </div>
        ))}

        {/* Clear All Link */}
        <button
          type="button"
          className="text-xs sm:text-sm font-bold text-[#84A43C] hover:text-[#73922f] hover:underline cursor-pointer focus:outline-none ml-2"
        >
          Clear All
        </button>
      </div>

      {/* Row 3: Sort by & View Toggle */}
      <div className="flex items-center justify-between border-t border-slate-100 pt-4 flex-wrap gap-4 w-full">
        {/* Sort Tabs */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs sm:text-sm font-bold text-slate-400">Sort by:</span>
          <div className="flex p-1 bg-white border border-slate-200/80 rounded-2xl text-xs sm:text-sm font-semibold">
            <button
              type="button"
              onClick={() => setSelectedSort('latest')}
              className={`px-4 py-1.5 rounded-xl cursor-pointer transition-all ${
                selectedSort === 'latest'
                  ? 'bg-[#84A43C]/10 text-[#84A43C] font-extrabold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Latest
            </button>
            <button
              type="button"
              onClick={() => setSelectedSort('relevance')}
              className={`px-4 py-1.5 rounded-xl cursor-pointer transition-all ${
                selectedSort === 'relevance'
                  ? 'bg-[#84A43C]/10 text-[#84A43C] font-extrabold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Relevance
            </button>
            <button
              type="button"
              onClick={() => setSelectedSort('closing')}
              className={`px-4 py-1.5 rounded-xl cursor-pointer transition-all ${
                selectedSort === 'closing'
                  ? 'bg-[#84A43C]/10 text-[#84A43C] font-extrabold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Closing Soon
            </button>
          </div>
        </div>

        {/* Count and Layout switch */}
        <div className="flex items-center gap-4 text-xs sm:text-sm font-semibold text-slate-500">
          <span>120 jobs found</span>
          
          <div className="flex items-center p-0.5 bg-slate-100/80 border border-slate-200/40 rounded-xl">
            <button
              type="button"
              onClick={() => setViewType('grid')}
              className={`p-2 rounded-lg transition-all cursor-pointer ${
                viewType === 'grid'
                  ? 'bg-white text-[#84A43C] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
              aria-label="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewType('list')}
              className={`p-2 rounded-lg transition-all cursor-pointer ${
                viewType === 'list'
                  ? 'bg-white text-[#84A43C] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
              aria-label="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Listings feed */}
      <div className="pt-2 w-full space-y-8">
        {viewType === 'list' ? (
          // Horizontal List View layout matching the Figma screenshot exactly
          <div className="space-y-4 w-full">
            {jobListings.map((job) => (
              <div 
                key={job.id} 
                className="bg-white rounded-3xl p-5 border border-slate-100 shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 hover:shadow-md transition-shadow group min-h-[120px] w-full"
              >
                {/* Left section: Logo + Job description details */}
                <div className="flex items-start gap-4 min-w-0 flex-grow">
                  {/* Square company avatar wrapper with border */}
                  <div className="w-14 h-14 rounded-2xl border border-slate-200/60 bg-white flex items-center justify-center shrink-0 shadow-xs">
                    {job.logoComponent}
                  </div>
                  
                  {/* Metadata & Title details */}
                  <div className="space-y-2 min-w-0 text-left">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-[#3562D6] leading-snug group-hover:text-[#2563EB] transition-colors truncate">
                        {job.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-500">
                      <span>{job.company}</span>
                      <CheckCircle2 className="w-4.5 h-4.5 text-[#8CC63F] fill-current text-white shrink-0" />
                    </div>

                    {/* Meta detail row */}
                    <div className="flex items-center gap-4 flex-wrap text-xs font-semibold text-slate-400">
                      <div className="flex items-center gap-1">
                        <Briefcase className="w-4 h-4 text-slate-400" />
                        <span>{job.department}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        <span>{job.location}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span>{job.type}</span>
                      </div>
                    </div>

                    {/* Skill tag list */}
                    <div className="flex items-center gap-2 flex-wrap pt-1 text-[11px] font-semibold text-slate-500">
                      {job.skills.map((skill) => (
                        <span key={skill} className="px-3 py-1 bg-[#FDF9F0] border border-slate-100 rounded-lg">
                          {skill}
                        </span>
                      ))}
                      <span className="px-2.5 py-1 bg-amber-500 text-white rounded-lg font-bold">
                        +{job.extraSkills}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Center metadata columns (Experience, Salary, Posted) */}
                <div className="flex items-center gap-8 sm:gap-12 shrink-0 flex-wrap lg:flex-nowrap w-full lg:w-auto border-t lg:border-t-0 pt-4 lg:pt-0 border-slate-50">
                  {/* Experience Column */}
                  <div className="text-left min-w-[80px]">
                    <p className="text-[#EF4444] font-extrabold text-base leading-tight">{job.experience}</p>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">Experience</p>
                  </div>

                  {/* Salary Column */}
                  <div className="text-left min-w-[100px]">
                    <p className="text-[#3562D6] font-extrabold text-base leading-tight">{job.salary}</p>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">Salary</p>
                  </div>

                  {/* Posted Column */}
                  <div className="text-left min-w-[80px]">
                    <p className="text-[#84A43C] font-extrabold text-base leading-tight">{job.posted}</p>
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">Posted</p>
                  </div>
                </div>

                {/* Right Action buttons */}
                <div className="flex items-center gap-3 shrink-0 w-full lg:w-auto border-t lg:border-t-0 pt-4 lg:pt-0 border-slate-50 justify-end">
                  <button
                    type="button"
                    onClick={() => toggleSaveJob(job.id)}
                    className={`p-3.5 border rounded-2xl transition-colors cursor-pointer ${
                      savedJobs.includes(job.id)
                        ? 'bg-rose-50 border-rose-200 text-[#EF4444]'
                        : 'bg-white hover:bg-rose-50/50 border-rose-100 text-[#EF4444] hover:text-[#EF4444]'
                    }`}
                    aria-label="Save Job"
                  >
                    <Heart className={`w-5 h-5 ${savedJobs.includes(job.id) ? 'fill-current' : ''}`} />
                  </button>
                  <button
                    type="button"
                    className="px-6 py-3 bg-[#8CC63F] hover:bg-[#7db535] active:scale-[0.99] text-white font-bold text-sm tracking-wide rounded-2xl shadow-sm transition-all duration-200 cursor-pointer w-full sm:w-auto text-center"
                  >
                    Apply Now
                  </button>
                </div>

              </div>
            ))}
          </div>
        ) : (
          // Grid View Layout
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
            {jobListings.map((job) => (
              <div key={job.id} className="relative bg-white rounded-[32px] p-6 shadow-xs border border-slate-100 flex flex-col justify-between overflow-hidden hover:shadow-md transition-shadow group min-h-[220px]">
                
                {/* Wave Corner Background Graphic */}
                <img
                  src={bgCorner}
                  alt="Wave background decoration"
                  className="absolute top-0 right-0 w-[130px] h-auto pointer-events-none select-none z-0 object-contain object-right-top"
                />

                <div className="relative z-10">
                  {/* Title & Department */}
                  <div className="text-left mb-4 pr-16">
                    <h3 className="text-base sm:text-lg font-bold text-[#3562D6] leading-snug group-hover:text-[#2563EB] transition-colors">
                      {job.title}
                    </h3>
                    <p className="text-xs sm:text-sm font-medium text-slate-500 mt-0.5">{job.company}</p>
                  </div>

                  {/* Metadata Details */}
                  <div className="space-y-2.5 text-xs sm:text-sm text-slate-600 font-semibold mb-6">
                    <div className="flex items-center gap-4 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <span className="text-amber-500 font-extrabold">🕒</span>
                        <span>{job.experience}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[#C026D3] font-extrabold">💼</span>
                        <span>{job.type}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span className="text-red-500 font-extrabold">📍</span>
                      <span>{job.location}</span>
                    </div>
                  </div>
                </div>

                {/* Apply Now Action Button */}
                <button 
                  type="button" 
                  className="relative z-10 w-full py-3 bg-[#8CC63F] hover:bg-[#7db535] active:scale-[0.99] text-white font-bold text-sm tracking-wide rounded-2xl shadow-sm transition-all duration-200 cursor-pointer"
                >
                  Apply Now
                </button>

              </div>
            ))}
          </div>
        )}

        {/* Pagination Row matching Figma specifications */}
        <div className="flex items-center justify-center gap-2 pt-6 select-none w-full">
          {/* Previous Page Arrow */}
          <button
            type="button"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            className="w-10 h-10 border border-slate-200 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all cursor-pointer"
            aria-label="Previous Page"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          {/* Page Numbers */}
          {[1, 2, 3, 4, 5].map((pageNum) => (
            <button
              key={pageNum}
              type="button"
              onClick={() => setCurrentPage(pageNum)}
              className={`w-10 h-10 rounded-xl font-bold text-sm transition-all cursor-pointer ${
                currentPage === pageNum
                  ? 'bg-[#84A43C] text-white shadow-xs'
                  : 'border border-slate-200 text-slate-500 hover:bg-slate-50'
              }`}
            >
              {pageNum}
            </button>
          ))}
          
          <span className="text-slate-400 px-1">...</span>

          <button
            type="button"
            onClick={() => setCurrentPage(10)}
            className={`w-10 h-10 rounded-xl font-bold text-sm transition-all cursor-pointer ${
              currentPage === 10
                ? 'bg-[#84A43C] text-white shadow-xs'
                : 'border border-slate-200 text-slate-500 hover:bg-slate-50'
            }`}
          >
            10
          </button>

          {/* Next Page Arrow */}
          <button
            type="button"
            onClick={() => setCurrentPage(prev => Math.min(10, prev + 1))}
            className="w-10 h-10 border border-slate-200 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all cursor-pointer"
            aria-label="Next Page"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

      </div>

    </div>
  );
}

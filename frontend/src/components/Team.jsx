/**
 * Team Component
 */

import React, { useState, useEffect } from 'react';

console.log('Team.jsx file loaded!');

export const Team = ({ currentUser, onInvite }) => {
  console.log('Team component rendering!', { currentUser });
  
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('all');

  const demoMembers = [
    {
      id: 1,
      full_name: 'Alex Vance',
      email: 'alex.vance@company.com',
      role: 'Principal Engineer',
      department: 'Engineering',
      isOnline: true,
      avatar: 'https://ui-avatars.com/api/?name=Alex+Vance&background=3B4AF5&color=fff'
    },
    {
      id: 2,
      full_name: 'Sarah Jenkins',
      email: 'sarah.jenkins@company.com',
      role: 'Senior Engineer',
      department: 'Engineering',
      isOnline: true,
      avatar: 'https://ui-avatars.com/api/?name=Sarah+Jenkins&background=25C2A0&color=fff'
    },
    {
      id: 3,
      full_name: 'Marcus Chen',
      email: 'marcus.chen@company.com',
      role: 'Engineering Manager',
      department: 'Engineering',
      isOnline: false,
      avatar: 'https://ui-avatars.com/api/?name=Marcus+Chen&background=FFB800&color=fff'
    },
    {
      id: 4,
      full_name: 'Priya Patel',
      email: 'priya.patel@company.com',
      role: 'Product Designer',
      department: 'Design',
      isOnline: true,
      avatar: 'https://ui-avatars.com/api/?name=Priya+Patel&background=3B4AF5&color=fff'
    },
    {
      id: 5,
      full_name: 'James Okafor',
      email: 'james.okafor@company.com',
      role: 'DevOps Lead',
      department: 'Engineering',
      isOnline: true,
      avatar: 'https://ui-avatars.com/api/?name=James+Okafor&background=25C2A0&color=fff'
    },
    {
      id: 6,
      full_name: 'Emily Rodriguez',
      email: 'emily.rodriguez@company.com',
      role: 'QA Lead',
      department: 'QA',
      isOnline: false,
      avatar: 'https://ui-avatars.com/api/?name=Emily+Rodriguez&background=FFB800&color=fff'
    },
    {
      id: 7,
      full_name: 'Michael Kim',
      email: 'michael.kim@company.com',
      role: 'Senior Developer',
      department: 'Engineering',
      isOnline: true,
      avatar: 'https://ui-avatars.com/api/?name=Michael+Kim&background=3B4AF5&color=fff'
    },
    {
      id: 8,
      full_name: 'Lisa Wong',
      email: 'lisa.wong@company.com',
      role: 'Product Manager',
      department: 'Product',
      isOnline: false,
      avatar: 'https://ui-avatars.com/api/?name=Lisa+Wong&background=25C2A0&color=fff'
    },
  ];

  useEffect(() => {
    console.log('Team useEffect running!');
    setMembers(demoMembers);
    setLoading(false);
  }, []);

  const departments = ['all', ...new Set(members.map(m => m.department))];
  const onlineCount = members.filter(m => m.isOnline).length;

  console.log('Team state:', { members: members.length, loading, onlineCount });

  const filteredMembers = members.filter(member => {
    const matchesSearch = 
      member.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.role.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesDepartment = selectedDepartment === 'all' || member.department === selectedDepartment;
    
    return matchesSearch && matchesDepartment;
  });

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-logic-blue border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-text-secondary">Loading team members...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
          <div>
            <h2 className="text-3xl font-bold text-text-primary">Team Members</h2>
            <p className="text-text-secondary mt-1">
              {members.length} members • {onlineCount} online now
            </p>
          </div>
          <button
            onClick={onInvite}
            className="bg-logic-blue text-white px-4 py-2 rounded-lg font-medium hover:bg-logic-blue-dark transition flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-lg">person_add</span>
            Invite Teammate
          </button>
        </div>

        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">search</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search members..."
                className="w-full pl-10 pr-4 py-2 bg-white border border-border rounded-lg focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
              />
            </div>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 flex-wrap">
            {departments.map((dept) => (
              <button
                key={dept}
                onClick={() => setSelectedDepartment(dept)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize whitespace-nowrap transition ${
                  selectedDepartment === dept
                    ? 'bg-terminal-indigo text-white'
                    : 'bg-white border border-border text-text-secondary hover:bg-surface-hover'
                }`}
              >
                {dept === 'all' ? 'All Departments' : dept}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMembers.map((member) => (
            <div key={member.id} className="bg-white border border-border rounded-xl p-5 hover:border-logic-blue hover:shadow-md transition-all">
              <div className="flex items-start gap-4">
                <div className="relative">
                  <img src={member.avatar} alt={member.full_name} className="w-14 h-14 rounded-full object-cover border-2 border-border" />
                  <span className={`absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-white ${member.isOnline ? 'bg-mint-success' : 'bg-text-muted'}`} title={member.isOnline ? 'Online' : 'Offline'} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-text-primary truncate">{member.full_name}</h3>
                  <p className="text-sm text-logic-blue font-medium truncate">{member.role}</p>
                  <p className="text-xs text-text-muted font-mono truncate mt-0.5">{member.email}</p>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-border flex items-center justify-between">
                <span className="text-xs font-mono font-medium text-text-secondary bg-surface-hover px-2 py-0.5 rounded">{member.department}</span>
                <span className={`text-xs font-medium ${member.isOnline ? 'text-mint-success' : 'text-text-muted'}`}>
                  {member.isOnline ? '● Online' : '○ Offline'}
                </span>
              </div>
            </div>
          ))}
        </div>

        {filteredMembers.length === 0 && (
          <div className="text-center py-16 bg-white border border-border rounded-lg">
            <span className="material-symbols-outlined text-5xl text-text-muted">group</span>
            <h3 className="text-xl font-semibold text-text-primary mt-3">No members found</h3>
            <p className="text-text-secondary mt-1">{searchQuery ? 'Try adjusting your search' : 'Invite team members to get started'}</p>
          </div>
        )}
      </div>
    </main>
  );
};

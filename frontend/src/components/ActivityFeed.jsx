/**
 * Activity Feed Component
 */

import React, { useState } from 'react';

export const ActivityFeed = ({ activities = [], onRefresh, limit = 10 }) => {
  const [visible, setVisible] = useState(limit);

  const getActivityIcon = (action) => {
    if (!action) return 'history';
    if (action.includes('created')) return 'add_circle';
    if (action.includes('updated') || action.includes('edited')) return 'edit';
    if (action.includes('moved')) return 'sync_alt';
    if (action.includes('deleted') || action.includes('archived')) return 'delete';
    if (action.includes('commented')) return 'chat_bubble';
    if (action.includes('assigned')) return 'person_add';
    return 'history';
  };

  const getActivityColor = (action) => {
    if (!action) return 'text-text-secondary';
    if (action.includes('created')) return 'text-mint-success';
    if (action.includes('updated')) return 'text-logic-blue';
    if (action.includes('moved')) return 'text-amber-urgency';
    if (action.includes('deleted')) return 'text-error';
    return 'text-text-secondary';
  };

  const displayedActivities = activities.slice(0, visible);

  return (
    <div className="bg-white border border-border rounded-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-logic-blue">history</span>
          Recent Activity
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-text-secondary hover:text-logic-blue transition p-1 rounded hover:bg-surface-hover"
          >
            <span className="material-symbols-outlined">refresh</span>
          </button>
        )}
      </div>

      <div className="space-y-4 relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border"></div>

        {displayedActivities.length === 0 ? (
          <p className="text-center text-text-secondary py-8">No activity yet</p>
        ) : (
          displayedActivities.map((activity, index) => (
            <div key={activity.id || index} className="flex gap-4 relative z-10">
              <div className={`w-8 h-8 rounded-full bg-surface-hover flex items-center justify-center shrink-0 border-2 border-white ${getActivityColor(activity.action)}`}>
                <span className="material-symbols-outlined text-sm">
                  {getActivityIcon(activity.action)}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-text-secondary">
                  <span className="font-semibold text-text-primary">
                    {activity.user || activity.author_name || 'Unknown'}
                  </span>
                  {' '}{activity.action || 'did something'}{' '}
                  {activity.target && (
                    <span className="font-medium text-text-primary">{activity.target}</span>
                  )}
                </p>
                <span className="text-xs text-text-muted">
                  {activity.timeAgo || activity.created_at || 'Just now'}
                </span>
              </div>
            </div>
          ))
        )}

        {activities.length > limit && visible < activities.length && (
          <button
            onClick={() => setVisible(visible + limit)}
            className="w-full text-center text-sm text-logic-blue hover:underline mt-2"
          >
            Load more...
          </button>
        )}
      </div>
    </div>
  );
};

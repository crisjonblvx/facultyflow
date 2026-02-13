import { Bell, Pin, Filter } from 'lucide-react';
import type { AnnouncementFilter } from '../types';

interface FilterBarProps {
  activeFilter: AnnouncementFilter;
  onFilterChange: (filter: AnnouncementFilter) => void;
  unreadCount: number;
}

const filters: { key: AnnouncementFilter; label: string; icon: React.ReactNode }[] = [
  { key: 'all', label: 'All', icon: <Filter className="w-4 h-4" /> },
  { key: 'urgent', label: 'Urgent', icon: <span className="text-sm">!</span> },
  { key: 'unread', label: 'Unread', icon: <Bell className="w-4 h-4" /> },
  { key: 'pinned', label: 'Pinned', icon: <Pin className="w-4 h-4" /> },
];

export default function FilterBar({ activeFilter, onFilterChange, unreadCount }: FilterBarProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {filters.map(({ key, label, icon }) => {
        const isActive = activeFilter === key;
        const displayLabel = key === 'unread' && unreadCount > 0
          ? `${label} (${unreadCount})`
          : label;

        return (
          <button
            key={key}
            onClick={() => onFilterChange(key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full font-semibold whitespace-nowrap text-sm transition-all min-h-[40px] ${
              isActive
                ? 'bg-navy-primary text-white shadow-md'
                : 'bg-white text-dark-gray border border-medium-gray hover:bg-light-gray'
            }`}
          >
            {icon}
            <span>{displayLabel}</span>
          </button>
        );
      })}
    </div>
  );
}

import { CheckCircle, Pin, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { Announcement } from '../types';

const urgencyConfig = {
  HIGH: { icon: '!', text: 'URGENT', bg: 'bg-error', ring: 'ring-error' },
  MEDIUM: { icon: '!', text: 'IMPORTANT', bg: 'bg-warning', ring: 'ring-warning' },
  LOW: { icon: 'i', text: 'FYI', bg: 'bg-success', ring: 'ring-success' },
};

interface AnnouncementCardProps {
  announcement: Announcement;
  onMarkRead: (id: number) => void;
  onTogglePin: (id: number, pinned: boolean) => void;
}

export default function AnnouncementCard({
  announcement,
  onMarkRead,
  onTogglePin,
}: AnnouncementCardProps) {
  const badge = urgencyConfig[announcement.urgency];

  // Strip HTML tags from message for preview
  const plainMessage = announcement.message.replace(/<[^>]*>/g, '').trim();

  return (
    <div
      className={`bg-white rounded-lg shadow-md overflow-hidden transition-all hover:shadow-lg ${
        !announcement.read_status ? 'ring-2 ring-student-blue' : ''
      }`}
    >
      {/* Urgency Banner */}
      <div className={`${badge.bg} text-white px-4 py-1.5 text-sm font-semibold flex items-center gap-2`}>
        <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold">
          {badge.icon}
        </span>
        <span>{badge.text}</span>
        {announcement.pinned && <Pin className="w-3.5 h-3.5 ml-auto" />}
      </div>

      <div className="p-4">
        {/* Course Name */}
        <div className="text-sm text-dark-gray mb-1">{announcement.course_name}</div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-text-primary mb-2">{announcement.title}</h3>

        {/* Message Preview */}
        <p className="text-dark-gray text-sm mb-3 line-clamp-3">{plainMessage}</p>

        {/* Meta */}
        <div className="flex items-center justify-between text-xs text-dark-gray mb-3">
          <span>
            {formatDistanceToNow(new Date(announcement.posted_at), { addSuffix: true })}
            {announcement.posted_by_name && ` by ${announcement.posted_by_name}`}
          </span>
          {!announcement.read_status && (
            <span className="flex items-center gap-1 text-student-blue font-semibold">
              <span className="w-1.5 h-1.5 bg-student-blue rounded-full" />
              New
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {!announcement.read_status && (
            <button
              onClick={() => onMarkRead(announcement.id)}
              className="flex-1 bg-student-blue text-white px-3 py-2 rounded-lg font-semibold text-sm hover:bg-student-blue/90 transition flex items-center justify-center gap-1.5 min-h-[44px]"
            >
              <CheckCircle className="w-4 h-4" />
              Mark Read
            </button>
          )}

          <button
            onClick={() => onTogglePin(announcement.id, announcement.pinned)}
            className={`px-3 py-2 rounded-lg font-semibold text-sm transition min-h-[44px] ${
              announcement.pinned
                ? 'bg-gold-accent text-white hover:bg-gold-accent/90'
                : 'bg-light-gray text-dark-gray hover:bg-medium-gray'
            }`}
            title={announcement.pinned ? 'Unpin' : 'Pin'}
          >
            <Pin className="w-4 h-4" />
          </button>

          {announcement.canvas_url && (
            <a
              href={announcement.canvas_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-light-gray text-dark-gray px-3 py-2 rounded-lg font-semibold text-sm hover:bg-medium-gray transition flex items-center gap-1.5 min-h-[44px]"
            >
              Canvas
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

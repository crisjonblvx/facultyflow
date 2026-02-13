import { useEffect } from 'react';
import { Bell, RefreshCw, CheckCheck } from 'lucide-react';
import { useAnnouncementStore } from '../stores/announcementStore';
import AnnouncementCard from '../components/AnnouncementCard';
import FilterBar from '../components/FilterBar';

export default function AnnouncementHub() {
  const {
    announcements,
    unreadCount,
    filter,
    loading,
    syncing,
    error,
    fetchAnnouncements,
    syncAnnouncements,
    markAsRead,
    togglePin,
    markAllRead,
    setFilter,
  } = useAnnouncementStore();

  // Load announcements on mount and when filter changes
  useEffect(() => {
    fetchAnnouncements();
  }, [filter, fetchAnnouncements]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(fetchAnnouncements, 60000);
    return () => clearInterval(interval);
  }, [fetchAnnouncements]);

  const handleSync = async () => {
    const result = await syncAnnouncements();
    if (result.new_count > 0) {
      // Could show a toast here in Phase 2
    }
  };

  const handleFilterChange = (newFilter: typeof filter) => {
    setFilter(newFilter);
  };

  return (
    <div className="min-h-screen bg-light-gray pb-4">
      {/* Header */}
      <div className="bg-white border-b border-medium-gray sticky top-[52px] z-10">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Announcements
            </h1>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllRead()}
                  className="text-xs text-dark-gray hover:text-student-blue transition flex items-center gap-1 px-2 py-1 rounded"
                  title="Mark all as read"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  Read all
                </button>
              )}
              <button
                onClick={handleSync}
                disabled={syncing}
                className="bg-student-blue text-white px-3 py-1.5 rounded-lg text-sm font-semibold hover:bg-student-blue/90 transition disabled:opacity-50 flex items-center gap-1.5 min-h-[36px]"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync'}
              </button>
            </div>
          </div>

          <FilterBar
            activeFilter={filter}
            onFilterChange={handleFilterChange}
            unreadCount={unreadCount}
          />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-4 py-4">
        {error && (
          <div className="bg-error/10 border border-error/20 text-error rounded-lg px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        {loading && announcements.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-10 h-10 border-3 border-student-blue border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-dark-gray">Loading announcements...</p>
          </div>
        ) : announcements.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">
              {filter === 'urgent' ? '!' : filter === 'pinned' ? '' : ''}
            </div>
            <h3 className="text-lg font-semibold text-dark-gray mb-2">
              {filter === 'all'
                ? 'No announcements yet'
                : filter === 'urgent'
                ? 'No urgent announcements'
                : filter === 'unread'
                ? "You're all caught up!"
                : 'No pinned announcements'}
            </h3>
            <p className="text-medium-gray text-sm">
              {filter === 'all'
                ? 'Hit Sync to check Canvas for announcements'
                : filter === 'unread'
                ? 'All announcements have been read'
                : 'Try a different filter'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {announcements.map((announcement) => (
              <AnnouncementCard
                key={announcement.id}
                announcement={announcement}
                onMarkRead={markAsRead}
                onTogglePin={togglePin}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

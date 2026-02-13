import { useEffect, useState } from 'react';
import { BookOpen, Plus, ArrowLeft, RotateCcw, Check, X, Loader2, Sparkles } from 'lucide-react';
import { useStudyStore } from '../stores/studyStore';
import api from '../lib/api';
import type { StudentCourse, Flashcard } from '../types';

type View = 'decks' | 'create' | 'study';

export default function FlashcardsPage() {
  const { decks, currentCards, decksLoading, cardsLoading, generating, fetchDecks, fetchCards, generateFlashcards, reviewCard } = useStudyStore();
  const [view, setView] = useState<View>('decks');
  const [courses, setCourses] = useState<StudentCourse[]>([]);

  // Create form
  const [selectedCourse, setSelectedCourse] = useState<number>(0);
  const [topic, setTopic] = useState('');
  const [notes, setNotes] = useState('');
  const [cardCount, setCardCount] = useState(10);

  // Study mode
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [studyDeckTitle, setStudyDeckTitle] = useState('');

  useEffect(() => {
    fetchDecks();
    loadCourses();
  }, [fetchDecks]);

  const loadCourses = async () => {
    try {
      const res = await api.get('/api/v1/student/courses');
      setCourses(res.data.courses);
    } catch { /* */ }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const deck = await generateFlashcards(selectedCourse, topic, notes, cardCount);
      // Go into study mode with new deck
      await fetchCards(deck.id);
      setStudyDeckTitle(topic);
      setCurrentIndex(0);
      setFlipped(false);
      setView('study');
    } catch { /* */ }
  };

  const openDeck = async (deckId: number, title: string) => {
    await fetchCards(deckId);
    setStudyDeckTitle(title);
    setCurrentIndex(0);
    setFlipped(false);
    setView('study');
  };

  const handleAnswer = (correct: boolean) => {
    const card = currentCards[currentIndex];
    if (card) reviewCard(card.id, correct);
    setFlipped(false);
    if (currentIndex < currentCards.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const currentCard: Flashcard | undefined = currentCards[currentIndex];
  const progress = currentCards.length > 0 ? ((currentIndex + 1) / currentCards.length) * 100 : 0;

  // ── DECKS LIST ──────────────────────────────────────────────
  if (view === 'decks') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2">
            <BookOpen className="w-5 h-5" /> Flashcards
          </h1>
          <button
            onClick={() => setView('create')}
            className="bg-student-blue text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-1.5 hover:bg-student-blue/90 transition"
          >
            <Plus className="w-4 h-4" /> Create
          </button>
        </div>

        {decksLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-student-blue" />
          </div>
        ) : decks.length === 0 ? (
          <div className="text-center py-12">
            <Sparkles className="w-12 h-12 text-student-blue/30 mx-auto mb-3" />
            <p className="text-dark-gray font-medium">No flashcard decks yet</p>
            <p className="text-sm text-dark-gray mt-1">Paste your notes and AI will create study cards</p>
            <button
              onClick={() => setView('create')}
              className="mt-4 bg-student-blue text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-student-blue/90 transition"
            >
              Create Your First Deck
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {decks.map((deck) => (
              <button
                key={deck.id}
                onClick={() => openDeck(deck.id, deck.title)}
                className="w-full bg-white rounded-xl shadow-sm p-4 hover:shadow-md transition text-left"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-text-primary">{deck.title}</h3>
                    {deck.description && (
                      <p className="text-xs text-dark-gray mt-0.5">{deck.description}</p>
                    )}
                  </div>
                  <span className="text-sm text-dark-gray bg-light-gray px-2.5 py-1 rounded-full">
                    {deck.card_count} cards
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── CREATE DECK ─────────────────────────────────────────────
  if (view === 'create') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <button
          onClick={() => setView('decks')}
          className="flex items-center gap-1 text-sm text-dark-gray mb-4 hover:text-navy-primary transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Decks
        </button>

        <h1 className="text-xl font-bold text-navy-primary mb-6 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-student-blue" /> Generate Flashcards
        </h1>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Course</label>
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(Number(e.target.value))}
              required
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base bg-white"
            >
              <option value={0} disabled>Select a course</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>{c.course_name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              placeholder="e.g., Chapter 5 — Cell Biology"
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Your Notes / Source Text
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              required
              rows={8}
              placeholder="Paste your class notes, textbook excerpts, or lecture slides here. AI will generate flashcards from this content."
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Number of Cards: {cardCount}
            </label>
            <input
              type="range"
              min={5}
              max={25}
              value={cardCount}
              onChange={(e) => setCardCount(Number(e.target.value))}
              className="w-full accent-student-blue"
            />
            <div className="flex justify-between text-xs text-dark-gray">
              <span>5</span>
              <span>25</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={generating || !selectedCourse || !topic || !notes}
            className="w-full bg-navy-primary text-white py-3 rounded-lg font-semibold hover:bg-navy-hover transition disabled:opacity-50 min-h-[48px] flex items-center justify-center gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating cards...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate {cardCount} Flashcards
              </>
            )}
          </button>
        </form>
      </div>
    );
  }

  // ── STUDY MODE ──────────────────────────────────────────────
  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <button
        onClick={() => { setView('decks'); setCurrentIndex(0); setFlipped(false); }}
        className="flex items-center gap-1 text-sm text-dark-gray mb-4 hover:text-navy-primary transition"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Decks
      </button>

      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-bold text-navy-primary">{studyDeckTitle}</h1>
        <span className="text-sm text-dark-gray">
          {currentIndex + 1} / {currentCards.length}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-medium-gray rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-student-blue rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {cardsLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-student-blue" />
        </div>
      ) : currentCard ? (
        <>
          {/* Card */}
          <button
            onClick={() => setFlipped(!flipped)}
            className="w-full bg-white rounded-2xl shadow-lg p-8 min-h-[250px] flex items-center justify-center text-center transition-all hover:shadow-xl"
          >
            <div>
              <p className="text-xs text-dark-gray uppercase tracking-wide mb-3">
                {flipped ? 'Answer' : 'Question'}
              </p>
              <p className={`text-lg font-medium text-text-primary ${flipped ? '' : ''}`}>
                {flipped ? currentCard.back : currentCard.front}
              </p>
              {!flipped && (
                <p className="text-xs text-dark-gray mt-4">Tap to reveal answer</p>
              )}
            </div>
          </button>

          {/* Answer buttons */}
          {flipped ? (
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => handleAnswer(false)}
                className="flex-1 bg-error/10 text-error py-3 rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-error/20 transition min-h-[48px]"
              >
                <X className="w-5 h-5" /> Missed It
              </button>
              <button
                onClick={() => handleAnswer(true)}
                className="flex-1 bg-success/10 text-success py-3 rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-success/20 transition min-h-[48px]"
              >
                <Check className="w-5 h-5" /> Got It
              </button>
            </div>
          ) : (
            <div className="mt-6 text-center">
              <button
                onClick={() => setFlipped(true)}
                className="text-student-blue text-sm font-medium"
              >
                Reveal Answer
              </button>
            </div>
          )}

          {/* End of deck */}
          {currentIndex === currentCards.length - 1 && flipped && (
            <div className="mt-6 text-center">
              <p className="text-dark-gray text-sm mb-3">You've finished the deck!</p>
              <button
                onClick={() => { setCurrentIndex(0); setFlipped(false); }}
                className="bg-student-blue text-white px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 mx-auto hover:bg-student-blue/90 transition"
              >
                <RotateCcw className="w-4 h-4" /> Study Again
              </button>
            </div>
          )}
        </>
      ) : (
        <p className="text-center text-dark-gray py-12">No cards in this deck</p>
      )}
    </div>
  );
}

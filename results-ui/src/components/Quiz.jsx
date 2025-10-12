import { useState } from 'react';
import { Api } from '../api';

export default function Quiz() {
  const [items, setItems] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('curated');
  const [started, setStarted] = useState(false);

  async function load(quizMode = mode) {
    setLoading(true);
    setError(null);
    setCurrentIndex(0);
    setSelectedAnswer(null);
    setAnswered(false);
    setCorrectCount(0);
    setFinished(false);
    setStarted(true);
    try {
      const data = await Api.quiz(quizMode === 'curated' ? 10 : 8, quizMode);
      setItems(data.items || []);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  }

  function handleAnswer(optionIndex) {
    if (answered) return;
    setSelectedAnswer(optionIndex);
    setAnswered(true);

    const current = items[currentIndex];
    if (optionIndex === current.correctIndex) {
      setCorrectCount(prev => prev + 1);
    }
  }

  function handleNext() {
    if (currentIndex < items.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setFinished(true);
    }
  }

  const current = items[currentIndex];
  const progress = items.length > 0 ? ((currentIndex + 1) / items.length) * 100 : 0;

  // Loading state
  if (loading) {
    return (
      <div className="card" style={{ padding: 32, textAlign: 'center' }}>
        <h2>Loading quiz...</h2>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="card" style={{ padding: 32, textAlign: 'center' }}>
        <div className="badge err" style={{ fontSize: '1.1em' }}>{error}</div>
        <button className="btn" onClick={() => load()} style={{ marginTop: 16 }}>Try Again</button>
      </div>
    );
  }

  // Start screen
  if (!started) {
    return (
      <div className="card" style={{ padding: 32, maxWidth: 600, margin: '0 auto' }}>
        <h2 style={{ marginTop: 0, marginBottom: 8, textAlign: 'center', fontSize: '2em' }}>🎯 Try Yourself</h2>
        <p style={{ textAlign: 'center', color: 'var(--muted)', marginBottom: 24 }}>
          Test your riddle-solving skills! Can you decode these deliberately oblique clues?
        </p>

        <div style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 12, fontSize: '1.1em', color: 'var(--text)' }}>Choose your challenge:</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label
              style={{
                padding: 16,
                border: mode === 'curated' ? '2px solid var(--accent-2)' : '2px solid rgba(255,255,255,0.12)',
                borderRadius: 10,
                cursor: 'pointer',
                background: mode === 'curated' ? 'rgba(88,199,168,0.12)' : 'rgba(255,255,255,0.03)',
                transition: 'all 0.2s'
              }}
              onClick={() => setMode('curated')}
            >
              <div className="row" style={{ gap: 8, alignItems: 'flex-start' }}>
                <input
                  type="radio"
                  name="quiz-mode"
                  checked={mode === 'curated'}
                  onChange={() => setMode('curated')}
                  style={{ marginTop: 4 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1.1em', marginBottom: 4, color: 'var(--text)' }}>
                    🎮 Curated Mode
                  </div>
                  <div style={{ fontSize: '0.9em', color: 'var(--muted)' }}>
                    10 hand-picked questions with easier riddles. Great for getting started!
                  </div>
                </div>
              </div>
            </label>

            <label
              style={{
                padding: 16,
                border: mode === 'random' ? '2px solid var(--accent-2)' : '2px solid rgba(255,255,255,0.12)',
                borderRadius: 10,
                cursor: 'pointer',
                background: mode === 'random' ? 'rgba(88,199,168,0.12)' : 'rgba(255,255,255,0.03)',
                transition: 'all 0.2s'
              }}
              onClick={() => setMode('random')}
            >
              <div className="row" style={{ gap: 8, alignItems: 'flex-start' }}>
                <input
                  type="radio"
                  name="quiz-mode"
                  checked={mode === 'random'}
                  onChange={() => setMode('random')}
                  style={{ marginTop: 4 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1.1em', marginBottom: 4, color: 'var(--text)' }}>
                    🔥 Random Mode
                  </div>
                  <div style={{ fontSize: '0.9em', color: 'var(--muted)' }}>
                    8 random questions from the full benchmark. Much harder!
                  </div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <button
          className="btn primary"
          onClick={() => load(mode)}
          style={{ width: '100%', padding: 16, fontSize: '1.2em' }}
        >
          Start Quiz
        </button>
      </div>
    );
  }

  // Results screen
  if (finished) {
    const percentage = Math.round((correctCount / items.length) * 100);
    let message = '';
    let emoji = '';

    if (percentage === 100) {
      message = 'Perfect score! You\'re a riddle master!';
      emoji = '🏆';
    } else if (percentage >= 80) {
      message = 'Excellent work! You really know your stuff!';
      emoji = '🌟';
    } else if (percentage >= 60) {
      message = 'Good job! You got most of them!';
      emoji = '👍';
    } else if (percentage >= 40) {
      message = 'Not bad! These riddles are tricky!';
      emoji = '💪';
    } else {
      message = 'These are tough! Want to try again?';
      emoji = '🎯';
    }

    return (
      <div className="card" style={{ padding: 32, maxWidth: 600, margin: '0 auto', textAlign: 'center' }}>
        <div style={{ fontSize: '4em', marginBottom: 16 }}>{emoji}</div>
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: '2em', color: 'var(--text)' }}>Quiz Complete!</h2>
        <p style={{ fontSize: '1.2em', color: 'var(--muted)', marginBottom: 24 }}>{message}</p>

        <div style={{
          padding: 24,
          background: 'rgba(88,199,168,0.12)',
          borderRadius: 12,
          marginBottom: 24,
          border: '2px solid var(--accent-2)'
        }}>
          <div style={{ fontSize: '3em', fontWeight: 'bold', color: 'var(--accent-2)', marginBottom: 8 }}>
            {correctCount}/{items.length}
          </div>
          <div style={{ fontSize: '1.5em', color: 'var(--text)' }}>
            {percentage}% Correct
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn primary"
            onClick={() => load(mode)}
            style={{ padding: '12px 24px', fontSize: '1.1em' }}
          >
            Play Again
          </button>
          <button
            className="btn"
            onClick={() => {
              setItems([]);
              setFinished(false);
              setCurrentIndex(0);
              setCorrectCount(0);
              setStarted(false);
            }}
            style={{ padding: '12px 24px', fontSize: '1.1em' }}
          >
            Change Mode
          </button>
        </div>
      </div>
    );
  }

  // Game screen - show current question
  if (!current) return null;

  const isCorrect = answered && selectedAnswer === current.correctIndex;
  const isWrong = answered && selectedAnswer !== current.correctIndex;

  return (
    <div className="card" style={{ padding: 32, maxWidth: 700, margin: '0 auto' }}>
      {/* Progress bar */}
      <div style={{ marginBottom: 24 }}>
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: 8, fontSize: '0.9em', color: 'var(--muted)' }}>
          <span>Question {currentIndex + 1} of {items.length}</span>
          <span>{correctCount} correct</span>
        </div>
        <div style={{
          height: 8,
          background: 'rgba(255,255,255,0.08)',
          borderRadius: 4,
          overflow: 'hidden'
        }}>
          <div style={{
            height: '100%',
            width: `${progress}%`,
            background: 'linear-gradient(90deg, var(--accent), var(--accent-2))',
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>

      {/* Question */}
      <div style={{
        padding: 24,
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 12,
        marginBottom: 24,
        minHeight: 80,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1px solid rgba(255,255,255,0.08)'
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '1.4em',
          textAlign: 'center',
          lineHeight: 1.4,
          color: 'var(--text)'
        }}>
          {current.question}
        </h3>
      </div>

      {/* Answer options */}
      <div style={{ display: 'grid', gap: 12, marginBottom: 24 }}>
        {current.options.map((opt, idx) => {
          const isSelected = selectedAnswer === idx;
          const isCorrectOption = idx === current.correctIndex;
          const showCorrect = answered && isCorrectOption;
          const showWrong = answered && isSelected && !isCorrectOption;

          let buttonStyle = {
            padding: '16px 20px',
            fontSize: '1.1em',
            border: '2px solid rgba(255,255,255,0.12)',
            borderRadius: 10,
            background: 'rgba(255,255,255,0.03)',
            color: 'var(--text)',
            cursor: answered ? 'default' : 'pointer',
            textAlign: 'left',
            transition: 'all 0.2s',
            fontWeight: 500
          };

          if (showCorrect) {
            buttonStyle.background = 'rgba(34,197,94,0.15)';
            buttonStyle.borderColor = 'var(--ok)';
            buttonStyle.color = 'var(--ok)';
          } else if (showWrong) {
            buttonStyle.background = 'rgba(239,68,68,0.15)';
            buttonStyle.borderColor = 'var(--err)';
            buttonStyle.color = 'var(--err)';
          }

          return (
            <button
              key={idx}
              onClick={() => handleAnswer(idx)}
              disabled={answered}
              style={buttonStyle}
              onMouseEnter={(e) => {
                if (!answered) {
                  e.target.style.borderColor = 'var(--accent-2)';
                  e.target.style.background = 'rgba(88,199,168,0.12)';
                }
              }}
              onMouseLeave={(e) => {
                if (!answered) {
                  e.target.style.borderColor = 'rgba(255,255,255,0.12)';
                  e.target.style.background = 'rgba(255,255,255,0.03)';
                }
              }}
            >
              <div className="row" style={{ alignItems: 'center', gap: 12 }}>
                <div style={{
                  minWidth: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: showCorrect ? 'var(--ok)' : showWrong ? 'var(--err)' : 'rgba(255,255,255,0.1)',
                  color: (showCorrect || showWrong) ? '#0c1220' : 'var(--muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '0.9em'
                }}>
                  {String.fromCharCode(65 + idx)}
                </div>
                <div style={{ flex: 1 }}>{opt}</div>
                {showCorrect && <span style={{ fontSize: '1.5em' }}>✓</span>}
                {showWrong && <span style={{ fontSize: '1.5em' }}>✗</span>}
              </div>
            </button>
          );
        })}
      </div>

      {/* Feedback and next button */}
      {answered && (
        <div style={{
          padding: 20,
          borderRadius: 10,
          background: isCorrect ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
          border: `2px solid ${isCorrect ? 'var(--ok)' : 'var(--err)'}`,
          marginBottom: 16
        }}>
          <div style={{
            fontSize: '1.2em',
            fontWeight: 'bold',
            color: isCorrect ? 'var(--ok)' : 'var(--err)',
            marginBottom: 8
          }}>
            {isCorrect ? '✓ Correct!' : '✗ Not quite!'}
          </div>
          <div style={{ color: 'var(--text)' }}>
            {isCorrect
              ? 'Great job!'
              : `The correct answer is: ${current.options[current.correctIndex]}`
            }
          </div>
        </div>
      )}

      {answered && (
        <button
          className="btn primary"
          onClick={handleNext}
          style={{ width: '100%', padding: 16, fontSize: '1.2em' }}
        >
          {currentIndex < items.length - 1 ? 'Next Question →' : 'See Results'}
        </button>
      )}
    </div>
  );
} 
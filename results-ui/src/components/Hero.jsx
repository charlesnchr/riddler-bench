import { LINKS } from '../config';
import { Link } from 'react-router-dom';

export default function Hero() {
  return (
    <div className="card hero">
      <div className="hero-title">Riddler Bench</div>
      <div className="hero-sub">Benchmarking LLMs on riddles and indirect clues</div>
      <p className="hero-desc">
        A lightweight evaluation harness for testing LLMs on deliberately oblique, riddle-like
        information retrieval questions. Instead of asking "What movie has hobbits?", we ask
        "A tale of circular jewelry and walking, where the shortest carry the greatest burden.".
        This tests lateral thinking and the ability to connect abstract clues to concrete knowledge.
      </p>
      <div className="actions">
        <a className="btn" href={LINKS.github} target="_blank" rel="noreferrer" aria-label="GitHub" title="GitHub">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" className="btn-icon">
            <path d="M12 .5A11.5 11.5 0 0 0 .5 12.38c0 5.26 3.41 9.72 8.15 11.3.6.1.82-.27.82-.59 0-.29-.01-1.05-.02-2.06-3.32.73-4.02-1.6-4.02-1.6-.55-1.43-1.35-1.81-1.35-1.81-1.1-.78.08-.77.08-.77 1.22.09 1.87 1.27 1.87 1.27 1.08 1.89 2.83 1.34 3.52 1.02.11-.8.42-1.34.77-1.65-2.65-.31-5.44-1.37-5.44-6.09 0-1.35.47-2.45 1.25-3.31-.13-.31-.54-1.57.12-3.27 0 0 1.01-.33 3.3 1.26a11.4 11.4 0 0 1 6 0c2.29-1.59 3.3-1.26 3.3-1.26.66 1.7.25 2.96.12 3.27.78.86 1.25 1.96 1.25 3.31 0 4.73-2.8 5.77-5.47 6.08.43.37.82 1.1.82 2.22 0 1.6-.02 2.89-.02 3.29 0 .32.22.7.83.58 4.73-1.58 8.13-6.05 8.13-11.3A11.5 11.5 0 0 0 12 .5Z"/>
          </svg>
          Code
        </a>
        <a className="btn" href={LINKS.readme} target="_blank" rel="noreferrer">README</a>
        <a className="btn" href={LINKS.dataset} target="_blank" rel="noreferrer">Dataset</a>
        <Link className="btn primary" to="/examples">Try Yourself</Link>
      </div>
    </div>
  );
} 
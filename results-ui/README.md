# Riddler Bench Results UI

A React frontend for visualizing benchmark results from the Riddler Bench framework.

## Local Development

```bash
# Install dependencies
npm install

# Run both frontend and backend
npm run dev

# Or run separately:
npm run server  # Backend on :4000
npm run client  # Frontend on :3000
```

## Vercel Deployment

This app is configured for Vercel deployment with:

- **Static frontend**: React app built and served statically
- **Serverless API**: Node.js API routes in `/api/` directory
- **Data access**: Reads benchmark results from `results/` directory

### Deploy to Vercel

1. Connect your repo to Vercel
2. Set environment variables if needed:
   - `RESULTS_DIR` - Path to results directory (default: `results`)
3. Deploy!

The app will automatically:
- Build the React frontend with `vercel-build` script
- Deploy API endpoints as serverless functions
- Route API calls to `/api/*` and frontend to `/*`

### Project Structure

```
results-ui/
├── src/           # React frontend source
├── server/        # Local development server
├── api/           # Vercel serverless functions
├── vercel.json    # Vercel configuration
└── build/         # Production build output
```
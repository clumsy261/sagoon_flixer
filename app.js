const TMDB_API_KEY = '5c71404cb0350cba8be2ae3b042cd103';
//TMDB_API_KEY=5c71404cb0350cba8be2ae3b042cd103
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w342';

const searchInput = document.getElementById('searchInput');
const moviesRow = document.getElementById('moviesRow');
const tvShowsRow = document.getElementById('tvShowsRow');
const loading = document.getElementById('loading');

searchInput.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    
    const query = e.target.value.trim();
    
    if (query.length < 2) {
        clearResults();
        return;
    }
    
    searchContent(query);
});

async function searchContent(query) {
    showLoading(true);
    clearResults();
    
    try {
        const [moviesRes, tvRes] = await Promise.all([
            fetch(`${TMDB_BASE_URL}/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(query)}`),
            fetch(`${TMDB_BASE_URL}/search/tv?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(query)}`)
        ]);
        
        const moviesData = await moviesRes.json();
        const tvData = await tvRes.json();
        
        renderResults(moviesData.results, moviesRow, 'movie');
        renderResults(tvData.results, tvShowsRow, 'tv');
        
    } catch (error) {
        console.error('Search error:', error);
    } finally {
        showLoading(false);
    }
}

function renderResults(items, container, type) {
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="empty-state">No results found</div>';
        return;
    }
    
    container.innerHTML = items.map(item => {
        const posterPath = item.poster_path ? `${IMAGE_BASE_URL}${item.poster_path}` : 'https://via.placeholder.com/200x300?text=No+Image';
        const title = type === 'movie' ? item.title : item.name;
        const year = type === 'movie' 
            ? (item.release_date ? item.release_date.split('-')[0] : '')
            : (item.first_air_date ? item.first_air_date.split('-')[0] : '');
        const tmdbId = item.id;
        
        return `
            <div class="content-card" data-id="${tmdbId}" data-type="${type}" data-title="${title}">
                <img src="${posterPath}" alt="${title}" loading="lazy">
                <div class="title">${title}</div>
                ${year ? `<div class="year">${year}</div>` : ''}
            </div>
        `;
    }).join('');
    
    container.querySelectorAll('.content-card').forEach(card => {
        card.addEventListener('click', () => {
            const id = card.dataset.id;
            const type = card.dataset.type;
            const title = card.dataset.title;
            const tmdbId = `${type === 'movie' ? 'tt' : ''}${id}`;
            
            console.log('Selected:', { title, type, tmdbId, rawId: id });
        });
    });
}

function clearResults() {
    moviesRow.innerHTML = '';
    tvShowsRow.innerHTML = '';
}

function showLoading(show) {
    loading.classList.toggle('hidden', !show);
}
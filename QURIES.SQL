SELECT m.title, AVG(r.rating) AS avg_rating 
FROM movies m 
JOIN ratings r ON m.movieId = r.movieId 
GROUP BY m.movieId 
ORDER BY avg_rating DESC 
LIMIT 1; 
SELECT 
    g.genre AS Genre,
    ROUND(AVG(r.rating), 3) AS Average_Rating,
    COUNT(r.rating) AS Total_Ratings
FROM ratings r
JOIN movie_genres mg ON r.movie_id = mg.movie_id
JOIN genres g ON mg.genre_id = g.genre_id
GROUP BY g.genre
ORDER BY Average_Rating DESC
LIMIT 5;
SELECT 
    director,
    COUNT(*) AS movie_count
FROM movies
WHERE director IS NOT NULL AND director <> 'Unknown'
GROUP BY director
ORDER BY movie_count DESC
LIMIT 1;
SELECT 
    m.year AS Year,
    ROUND(AVG(r.rating), 3) AS Average_Rating,
    COUNT(r.rating) AS Total_Ratings
FROM movies m
JOIN ratings r ON m.movie_id = r.movie_id
WHERE m.year IS NOT NULL
GROUP BY m.year
ORDER BY m.year;


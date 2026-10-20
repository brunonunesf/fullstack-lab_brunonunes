-- Retorne o nome de cada participante do evento, em ordem de nome.
-- Consulte users e registrations; o teste fornece o ID do evento.
SELECT users.name
FROM registrations
JOIN users ON registrations.user_id = users.id
WHERE registrations.event_id = :event_id
ORDER BY users.name;

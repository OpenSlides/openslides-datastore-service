select * from 
(select * from events ev where ev.fqid='collection_string/6') e 
left join events_to_collectionfields ec on e.id=ec.event_id
left join collectionfields c on ec.collectionfield_id=c.id
where c.collectionfield='A/b';
--- up to 25ms on first execution, down to 0.7ms on second execution (probably cached)

select max(position) from events where fqid='collection_string/5';
--- up to almost 100ms on first execution, down to about 1 on second one
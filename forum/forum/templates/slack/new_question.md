New question: <{{ basesite }}{% url 'forum:thread' q.id %}|{{ q.title }}>
with tags *{{ tags }}* by {{ q.author.display_name }}
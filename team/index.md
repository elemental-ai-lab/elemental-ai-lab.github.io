---
title: Team
kind: team
nav:
  order: 2
description: Current members and alumni of Elemental AI Lab.
---

# Team

{% if site.lab.recruiting != "" %}<p class="page-intro"><a href="{{ '/join/' | relative_url }}">{{ site.lab.recruiting }}</a></p>{% endif %}

<div class="team-groups">
{%- assign alphabetical = site.members | sort: 'family' -%}
{%- assign current = alphabetical | where_exp: 'person', "person.group != 'alum'" -%}
{%- for role in site.data.roles -%}
  {%- assign people = current | where: 'role', role.key -%}
  {%- if people.size > 0 %}
<div class="roster-group">
  <h2>{{ role.heading | escape }}</h2>
  <div class="roster">
    {%- for person in people %}{% include portrait.html person=person %}{% endfor %}
  </div>
</div>
  {%- endif -%}
{%- endfor -%}
{%- assign alumni = alphabetical | where: 'group', 'alum' -%}
{%- if alumni.size > 0 %}
<div class="roster-group">
  <h2>Alumni</h2>
  <div class="roster">
    {%- for person in alumni %}{% include portrait.html person=person %}{% endfor %}
  </div>
</div>
{%- endif %}
</div>

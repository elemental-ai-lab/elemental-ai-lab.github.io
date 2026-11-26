---
title: Home
kind: home
nav:
  order: 1
---
{% include move.html %}

# The building blocks of generative AI

Elemental AI Lab develops the fundamental methods behind generative AI: probabilistic models of how systems evolve in physical time, algorithms that quantify their uncertainty, and principled ways to act on it, from experimental design to inference-time steering. We build them with and for the physical and natural sciences and engineering.
{:.lead}

<aside class="move-note" aria-label="Location and recruitment">
  {%- if moved %}
  <p>We are based at the <a href="{{ site.move.to_url }}">{{ site.move.to_unit }}</a> at {{ site.move.to_institution }}. {{ site.lab.recruiting }}</p>
  {%- else %}
  <p><strong>From Amsterdam to Singapore.</strong> We move from the <a href="{{ site.move.from_url }}">{{ site.move.from_unit }}</a> at the {{ site.move.from_institution }} to the <a href="{{ site.move.to_url }}">{{ site.move.to_unit }}</a> at {{ site.move.to_institution }} in {{ site.move.month }}. {{ site.lab.recruiting }}</p>
  {%- endif %}
  {%- if site.lab.recruiting != "" %}
  <a class="move-link" href="{{ '/join/' | relative_url }}">Explore PhD and postdoc opportunities <svg class="action-icon" aria-hidden="true" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10h13m-5-5 5 5-5 5"/></svg></a>
  {%- endif %}
</aside>

{% include section.html %}

## Research

{% include research.html %}

{% if site.group_photo.image %}
{% include section.html %}
<figure class="group-photo">
  <img src="{{ site.group_photo.image | relative_url }}" alt="{{ site.group_photo.alt | escape }}" loading="lazy">
  {% if site.group_photo.caption %}<figcaption>{{ site.group_photo.caption | escape }}</figcaption>{% endif %}
</figure>
{% endif %}

{% if site.data.news.size > 0 %}
{% include section.html %}

## Lab news

{% assign updates = site.data.news | sort: 'date' | reverse %}
<ul class="news-list">
  {% for item in updates limit:3 %}{% include news-item.html %}{% endfor %}
</ul>
{% if updates.size > 3 %}
<details class="news-archive">
  <summary>Earlier news <span>({{ updates.size | minus: 3 }})</span></summary>
  <ul class="news-list">{% for item in updates offset:3 %}{% include news-item.html %}{% endfor %}</ul>
</details>
{% endif %}
{% endif %}

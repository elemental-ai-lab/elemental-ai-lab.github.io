---
title: Join
kind: join
nav:
  order: 3
description: PhD positions for August 2027, postdoctoral fellowships and student research visits at NTU Singapore.
---
{% include move.html %}
{%- assign now_s = site.time | date: '%s' | plus: 0 -%}
{%- assign adm_s = site.lab.admissions_deadline | date: '%s' | plus: 0 -%}
{%- assign npgs_s = site.lab.npgs_deadline | date: '%s' | plus: 0 -%}

# Join the lab

<div class="join-lead">
  {% if site.lab.join_lead != "" %}<p class="join-intro">{{ site.lab.join_lead }}</p>{% endif %}
  {% unless moved %}<p>We move from the {{ site.move.from_unit }} at the {{ site.move.from_institution }} to the {{ site.move.to_unit }} at {{ site.move.to_institution }} in {{ site.move.month }}.</p>{% endunless %}
</div>

<div class="join-section">
  <h2 id="topics">Research directions</h2>
  <p>Projects grow out of the lab’s four research directions. They are directions, not ready-made projects: most work combines more than one, and the details take shape together with you.</p>
  <ul class="questions">
    {%- for area in site.data.research %}
    <li><a href="{{ '/' | relative_url }}#{{ area.id }}">{{ area.title }}</a></li>
    {%- endfor %}
  </ul>
  <p class="questions-note">We are particularly drawn to problems that unfold in real, physical time.</p>
  <p class="who">We welcome excellent students and postdocs with mathematical maturity, from backgrounds such as statistics, mathematics, computer science, physics and engineering.</p>
</div>

<div class="join-section">
  <h2 id="apply">Apply for a PhD</h2>
  <div class="apply">
    <dl>
      <dt>Email</dt>
      <dd><a href="mailto:{{ site.lab.phd_email }}?subject={{ site.lab.phd_subject | uri_escape }}">{{ site.lab.phd_email }}</a></dd>
      <dt>Subject</dt>
      <dd><code>{{ site.lab.phd_subject }}</code></dd>
      <dt>Attach</dt>
      <dd>Your CV and full transcripts</dd>
      <dt>In the email</dt>
      <dd>A short, human-written note about what you would like to work on</dd>
    </dl>
    <p class="apply-required">This format is required.</p>
  </div>
  <p class="apply-next">Then <a href="https://gradadmissions.ntu.edu.sg/apply/">submit your application</a> to the <a href="https://www.ntu.edu.sg/computing/admissions/graduate-programmes/detail/ccds-phd-computing-datascience">PhD in Computing and Data Science</a> at NTU and name Christian Andersson Naesseth as your proposed supervisor.
  {% if now_s <= adm_s %}NTU’s <a href="https://www.ntu.edu.sg/admissions/graduate/radmissionguide">research admissions guide</a> gives {{ site.lab.admissions_deadline | date: '%-d %B %Y' }} as the last day to apply for the {{ site.lab.intake }} intake; the College of Computing and Data Science is not among the schools with an earlier deadline.{% else %}The application window that closed on {{ site.lab.admissions_deadline | date: '%-d %B %Y' }} has passed; see NTU’s <a href="https://www.ntu.edu.sg/admissions/graduate/radmissionguide">research admissions guide</a> for the next intake.{% endif %}
  {% if now_s <= npgs_s %}To be considered for the Nanyang President’s Graduate Scholarship, apply by {{ site.lab.npgs_deadline | date: '%-d %B %Y' }}.{% endif %}</p>
  <p class="apply-other">For postdoctoral fellowship applications and research visits, email <a href="mailto:{{ site.lab.email }}">{{ site.lab.email }}</a> with your CV, dates and funding route.</p>
</div>

<nav class="join-jumps" aria-label="Funding on this page">
  <a href="#phd">PhD funding</a>
  <a href="#postdocs">Postdoctoral fellowships</a>
  <a href="#visits">Research visits</a>
</nav>

<div class="join-category">
  <h2 id="phd">PhD funding</h2>
  {% include funding.html section='phd' more='Other doctoral funding' %}
</div>

<div class="join-category">
  <h2 id="postdocs">Postdoctoral fellowships</h2>
  {% include funding.html section='postdocs' more='Other postdoctoral funding' %}
</div>

<div class="join-category">
  <h2 id="visits">Research visits</h2>
  {% include funding.html section='visits' more='More visiting routes' %}
</div>

{%- assign checked = site.data.funding | map: 'checked' | sort | last %}
<p class="join-date">Funding information checked {{ checked | date: '%-d %B %Y' }} against each scheme’s official page, linked from its entry.</p>

---
layout: landing
---

:::{container}
:name: home-head

<div class="title-with-logo">
   <div class="brand-text">ACTIVEMODEL</div>
</div>
:::

<p class="lead" style="text-align: center; font-size: 1.25rem; color: var(--sy-c-text-muted); margin-bottom: 2rem;">
SQLModel with developer ergonomics. Make SQLModel act like ActiveRecord.
</p>

:::{container} buttons wrap
<a href="getting-started.html" class="btn-no-wrap">Get Started</a>
:::

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} {octicon}`zap` High Performance
Built on SQLModel and SQLAlchemy for maximum efficiency and modern async workflows.
:::

:::{grid-item-card} {octicon}`code` Developer Friendly
Clean, intuitive ActiveRecord-like API designed for rapid development and less boilerplate.
:::
::::

```{toctree}
:maxdepth: 2
:hidden:

Getting Started <getting-started>
API Reference <autoapi/index>
Changelog <changelog>
```

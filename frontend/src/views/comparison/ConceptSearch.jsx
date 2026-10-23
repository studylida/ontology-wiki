import React, {useEffect, useId, useState} from 'react';

export function ConceptSearch({label, value, concepts, onChange, excludeId, disabled}) {
  const id = useId();
  const [query, setQuery] = useState(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  useEffect(() => {if (value) setQuery(null);}, [value]);
  const selected = concepts.find(c => c.id === value);
  const normalize = text => String(text || '').normalize('NFKC').toLocaleLowerCase().replace(/[\s\p{P}\p{S}]/gu, '');
  const needle = normalize(query);
  const matches = needle ? concepts.filter(c => [c.title, c.engName, c.id, ...(c.aliases || [])].some(name => normalize(name).includes(needle))) : [];
  const choose = concept => { if (concept.id !== excludeId) {onChange(concept.id); setQuery(null); setOpen(false);} };
  return <div className="comparison-concept-search">
    <label htmlFor={id}>{label}</label>
    <div className="comparison-search-input">
      <input id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`}
        aria-activedescendant={open && matches[active] ? `${id}-option-${active}` : undefined}
        autoComplete="off" disabled={disabled} value={query === null ? selected?.title || '' : query}
        placeholder="등록명·영문명·약어로 검색" onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
        onChange={event => {setQuery(event.target.value); setActive(0); setOpen(true); if (value) onChange('');}}
        onKeyDown={event => {
          if (event.key === 'Escape') {setOpen(false); return;}
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {event.preventDefault(); setOpen(true); setActive(index => Math.max(0, Math.min(matches.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1))));}
          if (event.key === 'Enter' && open) {event.preventDefault(); if (matches[active]) choose(matches[active]);}
        }} />
      <button type="button" aria-label={`${label} 지우기`} disabled={disabled || !value && !query}
        onClick={() => {setQuery(''); onChange(''); setOpen(false);}}>×</button>
    </div>
    {selected && query === null && <small>{selected.engName} · {selected.id}</small>}
    {open && <div className="comparison-search-results" id={`${id}-list`} role="listbox" aria-label={`${label} 검색 결과`}>
      {!needle ? <p>검색어를 입력하고 등록 대상을 선택하세요.</p> : matches.length ? matches.map((concept, index) =>
        <button key={concept.id} id={`${id}-option-${index}`} type="button" role="option" aria-selected={value === concept.id}
          aria-disabled={concept.id === excludeId} className={active === index ? 'active' : ''}
          onMouseDown={event => event.preventDefault()} onClick={() => choose(concept)}>
          <strong>{concept.title}</strong><small>{concept.engName} · {concept.id}{concept.id === excludeId ? ' · 다른 쪽에서 선택됨' : ''}</small>
        </button>) : <p>일치하는 등록 대상이 없습니다. 다른 이름이나 약어로 찾아보세요.</p>}
    </div>}
  </div>;
}

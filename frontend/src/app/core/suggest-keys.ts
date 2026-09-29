export type SuggestNav = {active: number; picked: boolean};

export function suggestNav(): SuggestNav {
  return {active: -1, picked: false};
}

export function moveSuggest(event: KeyboardEvent, nav: SuggestNav, items: any[], choose: (item: any) => void, close: () => void) {
  const key = event.key;
  if (key === 'ArrowDown' || key === 'ArrowUp') {
    if (!items.length) return;
    event.preventDefault();
    if (key === 'ArrowDown') nav.active = nav.active >= items.length - 1 ? 0 : nav.active + 1;
    else nav.active = nav.active <= 0 ? items.length - 1 : nav.active - 1;
    const input = event.target as HTMLElement;
    setTimeout(() => input.parentElement?.querySelector('button.active')?.scrollIntoView({block: 'nearest'}));
  } else if (key === 'Enter' && nav.active >= 0 && items[nav.active]) {
    event.preventDefault();
    const item = items[nav.active];
    nav.active = -1;
    nav.picked = true;
    choose(item);
  } else if (key === 'Escape') {
    nav.active = -1;
    close();
  }
}

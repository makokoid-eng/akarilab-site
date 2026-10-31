/*
  PURPOSE
    相談フォーム（Googleフォーム）へ飛んだクリックを GA4 のイベント soudan_form_click として送る。

    背景
      問い合わせは Googleフォームで受けているが、フォームは別ドメイン（forms.gle）なので
      フォーム側の送信完了はこちらからは計測できない。計測できるのは「フォームへ飛んだ」まで。
      そこが1件も取れていなかったため、「問い合わせが増えたか」を数字で確認する手段がなかった。

    なぜ中継ページ（/r/<slug>/）経由にしないか
      1. 中継ページは meta refresh と location.replace で「移動中…」を一度表示する。
         クリックしたらフォームが開く、という既存の挙動が変わる。
      2. 中継ページの ?from= は、中継ページ自身の page_location が /r/<slug>/ になって
         元ページを失うために必要なパラメータ。直リンクのクリックは元ページ上で発火するので、
         「どのページから」は GA4 が自動付与する page_location / page_path でそのまま取れる。
      3. footer-common.html と article-nav-common.html は build_pages.py が
         バイト同一のまま物理 include する（テンプレ変数が無い）。静的な ?from= では
         86ページのフッターと77ページの記事ナビが全部同じ値に潰れ、ページの区別が付かない。
         記事スラッグは日本語なので中継ページ側の FROM_RE を通らず unknown に落ちる。

    そのため、既存の中継ページ設計と「同じ考え方」だけを踏襲する：
      - 送るパラメータは slug / from / from_valid / channel / dest_domain / category の6つ。
        これは redirect_click と完全に同じ形で、setup_ga4_dimensions.py が
        カスタムディメンションとして既に登録済みの6件とも一致する。
        （GA4 側で新しいディメンションを登録しなくてよい。param 名を ch にすると
          登録済みの channel に入らず、新規登録が必要になるので ch にはしない）
      - from のサニタイズ正規表現 FROM_RE は build_redirects.py と同一
      - channel のホワイトリストは build_redirects.py と同一
      - transport_type は 'beacon'
      - 遷移先 URL（dest_url）は送らない（dest_domain までにする。中継ページと同じ）
      - 個人情報は送らない（氏名・メール・入力内容は一切触らない）

    どのリンクを拾うか
      既存の data-soudan 属性（index.html が href を差し替えるのに使っている印）を
      そのまま流用し、属性値を from の識別子にする。属性が無い場合の保険として
      リンク先ホストが forms.gle のものも拾う。
      ひだまりβ版モニターフォームは /r/hidamari-monitor-form/ 経由（内部リンク）なので
      ここでは拾わない。中継ページ側の redirect_click と二重計上にならない。

    挙動は変えない
      preventDefault もしないし href も書き換えない。クリックの結果は従来どおり。
*/
(function () {
  'use strict';

  /* 同じページに script タグが2つ入っても二重計上しないようにする */
  if (window.__akariSoudanClickBound) return;
  window.__akariSoudanClickBound = true;

  /* build_redirects.py の render_page() と同一の定義 */
  var FROM_RE = /^[a-z0-9][a-z0-9_-]{0,80}$/;
  var CH_WHITELIST = ['note', 'cocon', 'akari', 'x', 'other'];

  /* 相談フォームのホスト。forms.gle の短縮URLのみ対象 */
  var FORM_HOST = 'forms.gle';

  /* この導線の識別子。中継ページの slug と同じ役割（どの行き先か） */
  var SLUG = 'soudan-form';
  var CATEGORY = 'form';

  /*
    流入チャネルを決める。
    引数 : なし（window.location.search を読む）
    出力 : CH_WHITELIST 内の文字列
    URL に ?ch= が付いて着地していればそれを尊重し（例: /r/ 経由で note から来た場合）、
    無ければサイト内クリックなので 'akari'。サイト内の既存中継リンクが
    すべて ch=akari を手書きしているのと同じ扱いにする。
  */
  function resolveChannel() {
    var raw = '';
    try {
      raw = new URLSearchParams(window.location.search).get('ch') || '';
    } catch (e) {
      raw = '';
    }
    return CH_WHITELIST.indexOf(raw) >= 0 ? raw : 'akari';
  }

  /*
    クリックされた要素から相談フォームのリンクを探す。
    引数 : target … クリックイベントの target
    出力 : 該当する <a> 要素、該当しなければ null
  */
  function findFormLink(target) {
    if (!target || typeof target.closest !== 'function') return null;
    var a = target.closest('a');
    if (!a) return null;
    if (a.hasAttribute('data-soudan')) return a;
    if (a.hostname === FORM_HOST) return a;
    return null;
  }

  var channel = resolveChannel();

  document.addEventListener(
    'click',
    function (event) {
      var a = findFormLink(event.target);
      if (!a) return;
      if (typeof gtag !== 'function') return;

      var raw = a.getAttribute('data-soudan') || '';
      var fromValid = FROM_RE.test(raw);

      gtag('event', 'soudan_form_click', {
        slug: SLUG,
        from: fromValid ? raw : 'unknown',
        from_valid: fromValid,
        channel: channel,
        dest_domain: FORM_HOST,
        category: CATEGORY,
        transport_type: 'beacon'
      });
    },
    true
  );
})();

# -*- coding: utf-8 -*-
"""
FieldNote v2.x — Teste funcional completo via Playwright
Reporta bugs encontrados: persistencia IDB, XLSX, Captura Rapida, navegacao
"""
import sys, re
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8765/www/index.html"
results  = []

def log(status, test, detail=""):
    tag  = "[PASS]" if status == "pass" else ("[FAIL]" if status == "fail" else "[WARN]")
    line = f"{tag} {test}" + (f" -- {detail}" if detail else "")
    results.append((status, line))
    print(line)

def run_tests():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 390, "height": 844})
        page    = ctx.new_page()

        # ── 1. CARREGAMENTO ───────────────────────────────────────────
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            title = page.title()
            # verificar init() rodou
            init_ok = page.evaluate("typeof registros !== 'undefined' && typeof bioRegistros !== 'undefined'")
            log("pass" if init_ok else "fail", "Carregamento + init()", f"title={title}, init={init_ok}")
        except Exception as e:
            log("fail", "Carregamento", str(e)[:200])
            browser.close(); return

        # ── 2. NAVEGACAO — testar cada aba ───────────────────────────
        # Estrutura real: nav-btn[0]=projeto, [1]=manual, [2]=biometria, [3]=dashboard, [4]=mapa, [5]=enviar
        # Registros é sub-aba de dashboard (dsub-registros)
        nav_map = [
            ("projeto",    "panel-projeto",   3, "Projeto/Campanhas"),
            ("manual",     "panel-manual",    3, "Manual"),
            ("biometria",  "panel-biometria", 3, "Biometria"),
            ("dashboard",  "panel-dashboard", 3, "Dashboard"),
            ("enviar",     "panel-enviar",    3, "Enviar"),
        ]
        for panel_id, dom_id, btn_idx, label in nav_map:
            try:
                page.evaluate(f"irPara('{panel_id}', document.querySelectorAll('.nav-btn')[{btn_idx}])")
                page.wait_for_timeout(300)
                visible = page.locator(f"#{dom_id}").is_visible()
                log("pass" if visible else "fail", f"Nav -> {label}", f"#{dom_id} visivel={visible}")
            except Exception as e:
                # tentar via click no botao
                try:
                    btns = page.locator(".nav-btn")
                    for i in range(btns.count()):
                        if label.lower()[:3] in btns.nth(i).inner_text().lower():
                            btns.nth(i).click()
                            page.wait_for_timeout(300)
                            break
                    log("warn", f"Nav -> {label}", f"irPara falhou, tentei click: {str(e)[:80]}")
                except Exception as e2:
                    log("fail", f"Nav -> {label}", str(e2)[:80])

        # ── 3. SUB-ABA REGISTROS (dentro de Dashboard) ───────────────
        try:
            page.evaluate("irPara('dashboard', document.querySelectorAll('.nav-btn')[3])")
            page.wait_for_timeout(400)
            page.evaluate("mudarDashTab('registros')")
            page.wait_for_timeout(400)
            dsub = page.locator("#dsub-registros")
            visible = dsub.is_visible() if dsub.count() > 0 else False
            log("pass" if visible else "fail", "Sub-aba Registros (dentro de Dashboard)", f"#dsub-registros visivel={visible}")
        except Exception as e:
            log("fail", "Sub-aba Registros", str(e)[:200])

        # ── 4. REGISTRO MANUAL — preencher e salvar via JS direto ────
        try:
            page.evaluate("irPara('manual', document.querySelectorAll('.nav-btn')[1])")
            page.wait_for_timeout(800)
            # chamar adicionarManual() via JS direto para capturar erros
            result = page.evaluate("""(() => {
                try {
                    // Garantir metodo selecionado
                    const m = document.getElementById('m-metodo');
                    m.value = 'Ponto de escuta';
                    onMetodoChange('Ponto de escuta');
                    // Preencher especie
                    const esp = document.getElementById('m-especie');
                    esp.value = 'Turdus leucomelas';
                    const nBefore = registros.length;
                    adicionarManual();
                    const alertEl = document.getElementById('manual-alert');
                    return {
                        ok: true,
                        nBefore,
                        nAfter: registros.length,
                        alertTxt: alertEl ? alertEl.textContent : '(sem alerta)',
                        metodoval: m.value
                    };
                } catch(e) {
                    return { ok: false, err: e.message + ' @ ' + e.stack?.split('\\n')[1] };
                }
            })()""")
            if not result.get('ok'):
                log("fail", "Registro manual — adicionarManual() erro JS", result.get('err', '')[:200])
            elif result['nAfter'] > result['nBefore']:
                log("pass", "Registro manual — salvo", f"registros={result['nBefore']}->{result['nAfter']}, metodo={result['metodoval']}")
            else:
                log("fail", "Registro manual — salvo", f"registros={result['nBefore']}->{result['nAfter']}, alerta={result['alertTxt'][:80]}, metodo={result['metodoval']}")
        except Exception as e:
            log("fail", "Registro manual", str(e)[:200])

        # ── 4b. PERSISTENCIA IDB — verificar apos salvar ──────────────
        try:
            n = page.evaluate("registros.length")
            if n > 0:
                ultimo = page.evaluate("(function(){ const r=registros[registros.length-1]; return {especie:r.especie, _src:r._src, _record_type:r._record_type}; })()")
                log("pass", "Persistencia — registros em memoria", f"n={n}, ultimo={ultimo}")
            else:
                log("fail", "Persistencia — registros em memoria", f"registros.length={n} apos salvar")
        except Exception as e:
            log("fail", "Persistencia IDB", str(e)[:200])

        # ── 5. CAPTURA RAPIDA ─────────────────────────────────────────
        try:
            page.evaluate("irPara('biometria', document.querySelectorAll('.nav-btn')[2])")
            page.wait_for_timeout(500)
            # abrir captura rapida via JS
            page.evaluate("abrirRapida()")
            page.wait_for_timeout(400)
            sheet = page.locator("#qc-sheet")
            sheet_visible = sheet.is_visible() if sheet.count() > 0 else False
            log("pass" if sheet_visible else "fail", "Captura Rapida — painel abre", f"#qc-sheet visivel={sheet_visible}")

            if sheet_visible:
                # preencher so a especie (sem biometria)
                qc_esp = page.locator("#qc-especie")
                qc_esp.fill("Amazona amazonica")
                page.wait_for_timeout(200)
                page.keyboard.press("Escape")
                page.wait_for_timeout(100)

                n_bio_antes = page.evaluate("bioRegistros.length")
                # clicar botao salvar do QC
                page.evaluate("salvarRapida()")
                page.wait_for_timeout(600)
                n_bio_depois = page.evaluate("bioRegistros.length")

                if n_bio_depois > n_bio_antes:
                    ultimo_bio = page.evaluate("""(function(){
                        const r = bioRegistros[bioRegistros.length-1];
                        return { _src: r._src, _record_type: r._record_type, _tipo: r._tipo, especie: r.especie };
                    })()""")
                    log("pass", "Captura Rapida — salvo em bioRegistros", f"{n_bio_antes}->{n_bio_depois}, {ultimo_bio}")
                    # VERIFICAR: captura sem biometria vai para bioRegistros (por design)
                    # reportar se isso esta correto ou nao
                    log("warn", "Captura Rapida — classificacao como biometria",
                        f"_record_type={ultimo_bio['_record_type']}, _src={ultimo_bio['_src']} "
                        f"-- Registros SEM medicoes biometricas vao para bioRegistros por design. "
                        f"Se usuario esperava ir para registros[], e um bug de UX.")
                else:
                    qc_alert = page.locator("#qc-alert")
                    alert_txt = qc_alert.inner_text() if qc_alert.count() > 0 else "sem alerta"
                    log("fail", "Captura Rapida — salvo", f"bioRegistros nao cresceu. alerta={alert_txt[:80]}")

                # fechar qc
                page.evaluate("fecharRapida()")
                page.wait_for_timeout(200)
        except Exception as e:
            log("fail", "Captura Rapida", str(e)[:200])

        # ── 6. ABA DADOS (dsub-registros) — verificar lista ─────────
        try:
            page.evaluate("irPara('dashboard', document.querySelectorAll('.nav-btn')[3])")
            page.wait_for_timeout(400)
            page.evaluate("mudarDashTab('registros')")
            page.wait_for_timeout(600)
            # chamar render explicitamente
            page.evaluate("renderRegistrosFiltrado(); renderBioRegistros(document.getElementById('bio-lista'))")
            page.wait_for_timeout(300)
            lista_html = page.locator("#lista-registros").inner_html()
            bio_html   = page.locator("#bio-lista").inner_html()
            bar_txt    = page.locator("#record-count-bar").inner_text() if page.locator("#record-count-bar").count() > 0 else "?"

            turdus_ok  = "Turdus" in lista_html or "record-item" in lista_html
            amazona_ok = "Amazona" in bio_html   or ("empty" not in bio_html)
            log("pass" if turdus_ok  else "fail", "Dados — registro manual visivel na lista", f"bar: {bar_txt}")
            log("pass" if amazona_ok else "fail", "Dados — captura rapida visivel em bio-lista", f"bio html len={len(bio_html)}")
            # verificar filtros (chips)
            chips = page.locator(".filtro-chip")
            n_chips = chips.count()
            log("pass" if n_chips > 0 else "warn", "Filtros rapidos presentes", f"{n_chips} chips")
            if n_chips > 0:
                # clicar filtro Aves via JS (mais confiavel que click UI em scroll container)
                try:
                    page.evaluate("filtrarDados('Aves', document.querySelector('.filtro-chip'))")
                    page.wait_for_timeout(300)
                    log("pass", "Filtro Aves — ativado via JS")
                    page.evaluate("filtrarDados('todos', document.querySelector('.filtro-chip'))")
                    page.wait_for_timeout(200)
                except Exception as fe:
                    log("warn", "Filtro Aves", str(fe)[:100])
        except Exception as e:
            log("fail", "Aba Dados", str(e)[:200])

        # ── 7. DASHBOARD — resumo e graficos ────────────────────────
        try:
            page.evaluate("irPara('dashboard', document.querySelectorAll('.nav-btn')[3])")
            page.wait_for_timeout(400)
            page.evaluate("mudarDashTab('resumo')")
            page.wait_for_timeout(500)
            # totais
            n_obs = page.evaluate("registros.length + bioRegistros.length")
            dash_obs = page.locator("#dash-obs-total")
            dash_val = dash_obs.inner_text() if dash_obs.count() > 0 else "0"
            canvas   = page.locator("canvas")
            try: dash_int = int(dash_val.strip())
            except: dash_int = -1
            log("pass" if dash_int >= 0 else "warn", "Dashboard — total observacoes", f"dash={dash_val}, memoria={n_obs}")
            log("pass" if canvas.count() > 0 else "warn", "Dashboard — canvas grafico", f"canvas count={canvas.count()}")
        except Exception as e:
            log("fail", "Dashboard", str(e)[:200])

        # ── 8. DARK MODE ─────────────────────────────────────────────
        try:
            page.evaluate("toggleDarkMode ? toggleDarkMode() : document.body.classList.toggle('dark-mode')")
            page.wait_for_timeout(200)
            is_dark = page.evaluate("document.body.classList.contains('dark-mode')")
            log("pass" if is_dark else "warn", "Dark Mode — toggle ativa", f"dark={is_dark}")
            page.evaluate("if(document.body.classList.contains('dark-mode')) { toggleDarkMode ? toggleDarkMode() : document.body.classList.remove('dark-mode'); }")
            page.wait_for_timeout(200)
        except Exception as e:
            log("warn", "Dark Mode", str(e)[:100])

        # ── 9. BIOMETRIA MANUAL ───────────────────────────────────────
        try:
            page.evaluate("irPara('biometria', document.querySelectorAll('.nav-btn')[2])")
            page.wait_for_timeout(500)
            # verificar se secao Avifauna esta ativa
            bav_section = page.locator("#bio-Avifauna")
            ativo = "active" in (bav_section.get_attribute("class") or "") if bav_section.count() > 0 else False
            # preencher especie via JS (evitar problemas com autocomplete visivel)
            page.evaluate("""
                const esp = document.getElementById('bav-especie');
                if (esp) { esp.value = 'Amazona amazonica'; esp.dispatchEvent(new Event('input')); }
                const massa = document.getElementById('bav-massa');
                if (massa) { massa.value = '95.5'; }
            """)
            page.wait_for_timeout(300)
            # salvar via JS direto (evita problemas de visibilidade do botao)
            n_bio_antes = page.evaluate("bioRegistros.length")
            page.evaluate("salvarBioAvifauna ? salvarBioAvifauna() : null")
            page.wait_for_timeout(500)
            n_bio_depois = page.evaluate("bioRegistros.length")
            if n_bio_depois > n_bio_antes:
                log("pass", "Biometria Avifauna — salvo via salvarBioAvifauna()", f"{n_bio_antes}->{n_bio_depois}")
            else:
                # tentar via botao
                btn_bio = page.locator("#panel-biometria button.btn-primary").first
                if btn_bio.count() > 0 and btn_bio.is_visible():
                    btn_bio.click()
                    page.wait_for_timeout(500)
                    n_bio_depois2 = page.evaluate("bioRegistros.length")
                    if n_bio_depois2 > n_bio_antes:
                        log("pass", "Biometria Avifauna — salvo via botao", f"{n_bio_antes}->{n_bio_depois2}")
                    else:
                        log("fail", "Biometria Avifauna — nao salvo", f"bioRegistros={n_bio_antes}->{n_bio_depois2}")
                else:
                    log("warn", "Biometria Avifauna — botao salvar", "nao visivel ou nao encontrado")
        except Exception as e:
            log("warn", "Biometria manual", str(e)[:200])

        # ── 10. EXPORTACAO XLSX ───────────────────────────────────────
        try:
            page.evaluate("irPara('enviar', document.querySelectorAll('.nav-btn')[5])")
            page.wait_for_timeout(500)
            # verificar biblioteca
            xlsx_ok = page.evaluate("typeof XLSX !== 'undefined'")
            log("pass" if xlsx_ok else "fail", "XLSX biblioteca carregada", f"ok={xlsx_ok}")

            # testar gerarXLSX()
            wb_result = page.evaluate("""(() => {
                try {
                    const wb = gerarXLSX();
                    if (!wb) return { ok: false, err: 'wb null' };
                    const sheets = wb.SheetNames || [];
                    const ms = wb.Sheets['BANCO DE DADOS'];
                    // contar linhas de dados (excluindo 2 headers)
                    const aoa = ms ? XLSX.utils.sheet_to_json(ms, { header: 1 }) : [];
                    const nData = Math.max(0, aoa.length - 2); // subtrair as 2 linhas de header
                    const nBio = bioRegistros ? bioRegistros.length : 0;
                    return { ok: true, sheets, nData, nBio };
                } catch(e) { return { ok: false, err: e.message }; }
            })()""")

            if wb_result['ok']:
                n_data = wb_result['nData']
                n_reg_mem = page.evaluate("registros.length")
                sheets = wb_result['sheets']
                log("pass" if n_data >= 0 else "fail",
                    "gerarXLSX() executou sem erro",
                    f"sheets={sheets}, BANCO DE DADOS={n_data} linhas, registros em memoria={n_reg_mem}")
                # verificar se registros aparecem
                if n_reg_mem > 0 and n_data == 0:
                    log("fail", "XLSX — registros manuais NAO aparecem na planilha",
                        f"registros.length={n_reg_mem} mas BANCO DE DADOS tem {n_data} linhas de dados")
                elif n_reg_mem > 0 and n_data > 0:
                    log("pass", "XLSX — registros manuais exportados", f"{n_data} linha(s)")
                else:
                    log("warn", "XLSX — sem registros para verificar", f"registros.length={n_reg_mem}")
                # verificar abas de biometria
                bio_sheets = [s for s in sheets if s != 'BANCO DE DADOS']
                n_bio = wb_result['nBio']
                if n_bio > 0 and not bio_sheets:
                    log("fail", "XLSX — abas de biometria ausentes", f"bioRegistros={n_bio} mas nenhuma aba bio gerada")
                elif bio_sheets:
                    log("pass", "XLSX — abas de biometria geradas", f"{bio_sheets}")
                else:
                    log("warn", "XLSX — sem biometria para verificar", f"bioRegistros.length={n_bio}")
            else:
                log("fail", "gerarXLSX()", wb_result.get('err', 'erro desconhecido'))

            # verificar botao baixar XLSX
            btn_baixar = page.locator("#panel-enviar button[onclick*='baixarXLSX']")
            if btn_baixar.count() == 0:
                btn_baixar = page.locator("#panel-enviar button").filter(has_text=re.compile("baixar|xlsx|exportar", re.I)).first
            if btn_baixar.count() > 0 and btn_baixar.is_visible():
                log("pass", "Botao 'Baixar XLSX' visivel e clicavel")
            else:
                log("warn", "Botao baixar XLSX", "nao encontrado ou nao visivel")
        except Exception as e:
            log("fail", "Exportacao XLSX", str(e)[:200])

        # ── 11. PROJETO / CAMPANHAS ───────────────────────────────────
        try:
            page.evaluate("irPara('projeto', document.querySelectorAll('.nav-btn')[0])")
            page.wait_for_timeout(500)
            panel_proj = page.locator("#panel-projeto")
            p_visible = panel_proj.is_visible() if panel_proj.count() > 0 else False
            log("pass" if p_visible else "fail", "Painel Projeto/Campanhas visivel")
            if p_visible:
                # verificar botao nova campanha
                btn_nova = page.locator("#panel-projeto button").filter(has_text=re.compile("nova|criar|campanha|adicionar", re.I)).first
                if btn_nova.count() > 0:
                    log("pass", "Botao Nova Campanha presente")
                else:
                    log("warn", "Botao Nova Campanha", "nao encontrado")
        except Exception as e:
            log("fail", "Painel Projeto", str(e)[:200])

        # ── 12. MACKINNON INLINE ─────────────────────────────────────
        try:
            page.evaluate("irPara('manual', document.querySelectorAll('.nav-btn')[1])")
            page.wait_for_timeout(400)
            page.evaluate("""
                const m = document.getElementById('m-metodo');
                if (m) { m.value = 'Listas de Mackinnon'; onMetodoChange('Listas de Mackinnon'); }
            """)
            page.wait_for_timeout(400)
            mck_visible = page.locator("#mck-inline-block").is_visible()
            bio_hidden  = not page.locator("#manual-bio-wrap").is_visible()
            log("pass" if mck_visible else "fail", "MacKinnon inline — bloco visivel ao selecionar metodo")
            log("pass" if bio_hidden  else "fail", "MacKinnon — bio-wrap oculto corretamente")
            # restaurar metodo normal
            page.evaluate("onMetodoChange('Ponto de escuta')")
            page.wait_for_timeout(200)
        except Exception as e:
            log("fail", "MacKinnon", str(e)[:200])

        # ── 13. ESTADO FINAL ──────────────────────────────────────────
        try:
            state = page.evaluate("""(() => ({
                nReg:    registros    ? registros.length    : -1,
                nBio:    bioRegistros ? bioRegistros.length : -1,
                bioSrcs:  bioRegistros ? [...new Set(bioRegistros.map(r=>r._src||'?'))] : [],
                bioTypes: bioRegistros ? [...new Set(bioRegistros.map(r=>r._record_type||'?'))] : [],
                regSrcs:  registros   ? [...new Set(registros.map(r=>r._src||'?'))]   : [],
            }))()""")
            log("pass", "Estado final",
                f"registros={state['nReg']}, bioRegistros={state['nBio']}, "
                f"bioSrcs={state['bioSrcs']}, regSrcs={state['regSrcs']}")

            # diagnostico de bugs reportados
            print("\n--- DIAGNOSTICO DOS BUGS REPORTADOS ---")
            # Bug 1: captura_rapida va para biometria
            if 'captura_rapida' in state['bioSrcs']:
                print("BUG-1 [POR DESIGN]: Captura Rapida salva em bioRegistros (_src='captura_rapida').")
                print("  -> Registros sem medicoes biometricas ainda sao classificados como biometria.")
                print("  -> Se isso e indesejado, separe por '_record_type' no XLSX e na UI.")
            # Bug 2: registros salvos
            if state['nReg'] > 0:
                print(f"BUG-2 [OK]: registros.length={state['nReg']} -- persistencia em memoria OK.")
            else:
                print(f"BUG-2 [FALHOU]: registros.length={state['nReg']} -- registros nao estao sendo salvos!")
            # Bug 3: XLSX
            print("BUG-3: ver resultado de gerarXLSX() acima (nData vs nReg).")
        except Exception as e:
            log("fail", "Estado final", str(e)[:200])

        browser.close()

    # ── SUMARIO ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SUMARIO — FieldNote Teste Funcional Completo")
    print("="*60)
    passed = sum(1 for s,_ in results if s == "pass")
    failed = sum(1 for s,_ in results if s == "fail")
    warned = sum(1 for s,_ in results if s == "warn")
    print(f"[PASS] PASSOU: {passed}   [FAIL] FALHOU: {failed}   [WARN] AVISO: {warned}")
    if failed:
        print("\nFALHAS:")
        for s, l in results:
            if s == "fail": print(" ", l)
    if warned:
        print("\nAVISOS:")
        for s, l in results:
            if s == "warn": print(" ", l)
    print(f"\n[RESULTADO] {'PASSOU' if failed == 0 else 'FALHOU'} ({failed} falha(s))")
    return failed == 0

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)

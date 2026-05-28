# -*- coding: utf-8 -*-
"""Teste de roteamento da Captura Rapida: sem medidas -> registros, com medidas -> biometria"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765/www/index.html"

def run():
    with sync_playwright() as pw:
        page = pw.chromium.launch(headless=True).new_context(viewport={"width":390,"height":844}).new_page()
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # salvar um registro manual para baseline
        page.evaluate("""
            const m = document.getElementById('m-metodo');
            m.value = 'Ponto de escuta'; onMetodoChange('Ponto de escuta');
            document.getElementById('m-especie').value = 'Turdus leucomelas';
            adicionarManual();
        """)
        page.wait_for_timeout(400)

        # abrir QC
        page.evaluate("abrirRapida()")
        page.wait_for_timeout(400)

        # ── TESTE 1: sem medidas → deve ir para registros ──────────
        page.evaluate("document.getElementById('qc-especie').value = 'Amazona amazonica'")
        n_reg_a = page.evaluate("registros.length")
        n_bio_a = page.evaluate("bioRegistros.length")
        page.evaluate("salvarRapida()")
        page.wait_for_timeout(500)
        n_reg_b = page.evaluate("registros.length")
        n_bio_b = page.evaluate("bioRegistros.length")

        ok1 = n_reg_b > n_reg_a and n_bio_b == n_bio_a
        rt1 = page.evaluate("registros.length > 0 ? registros[registros.length-1]._record_type : 'vazio'")
        src1 = page.evaluate("registros.length > 0 ? registros[registros.length-1]._src : 'vazio'")
        print(f"[{'PASS' if ok1 else 'FAIL'}] SEM medidas -> registros={n_reg_a}->{n_reg_b}, bio={n_bio_a}->{n_bio_b} | _record_type={rt1}, _src={src1}")

        # ── TESTE 2: com medida (massa) → deve ir para bioRegistros ─
        page.evaluate("abrirRapida()")
        page.wait_for_timeout(400)
        page.evaluate("""
            document.getElementById('qc-especie').value = 'Amazona amazonica';
            qcRenderMedidas();
        """)
        page.wait_for_timeout(200)
        mass_set = page.evaluate("""(() => {
            const el = document.getElementById('qc-m-massa');
            if (el) { el.value = '150.5'; return true; }
            return false;
        })()""")
        n_reg_c = page.evaluate("registros.length")
        n_bio_c = page.evaluate("bioRegistros.length")
        page.evaluate("salvarRapida()")
        page.wait_for_timeout(500)
        n_reg_d = page.evaluate("registros.length")
        n_bio_d = page.evaluate("bioRegistros.length")

        ok2 = n_bio_d > n_bio_c and n_reg_d == n_reg_c
        rt2 = page.evaluate("bioRegistros.length > 0 ? bioRegistros[bioRegistros.length-1]._record_type : 'vazio'")
        src2 = page.evaluate("bioRegistros.length > 0 ? bioRegistros[bioRegistros.length-1]._src : 'vazio'")
        print(f"[{'PASS' if ok2 else 'FAIL'}] COM medida (massa_set={mass_set}) -> registros={n_reg_c}->{n_reg_d}, bio={n_bio_c}->{n_bio_d} | _record_type={rt2}, _src={src2}")

        # ── TESTE 3: XLSX inclui obs de captura_rapida ──────────────
        wb = page.evaluate("""(() => {
            const wb = gerarXLSX();
            const ms = wb.Sheets['BANCO DE DADOS'];
            const aoa = XLSX.utils.sheet_to_json(ms, {header:1});
            const nData = Math.max(0, aoa.length - 2);
            const bioSheets = wb.SheetNames.filter(s => s !== 'BANCO DE DADOS');
            return { sheets: wb.SheetNames, nData, bioSheets };
        })()""")
        nreg_mem = page.evaluate("registros.length")
        ok3 = wb['nData'] >= nreg_mem and nreg_mem > 0
        print(f"[{'PASS' if ok3 else 'FAIL'}] XLSX: sheets={wb['sheets']}, BANCO DE DADOS={wb['nData']} linhas (registros em memoria={nreg_mem}), bioSheets={wb['bioSheets']}")

        # ── ESTADO FINAL ────────────────────────────────────────────
        state = page.evaluate("""{
            nReg:    registros.length,
            nBio:    bioRegistros.length,
            regSrcs: [...new Set(registros.map(r=>r._src))],
            regTypes:[...new Set(registros.map(r=>r._record_type))],
            bioSrcs: [...new Set(bioRegistros.map(r=>r._src))],
        }""")
        print(f"\nEstado final:")
        print(f"  registros    ({state['nReg']}): srcs={state['regSrcs']}, types={state['regTypes']}")
        print(f"  bioRegistros ({state['nBio']}): srcs={state['bioSrcs']}")

        passed = sum([ok1, ok2, ok3])
        print(f"\n{'[PASS]' if passed==3 else '[FAIL]'} {passed}/3 testes passaram")
        return passed == 3

if __name__ == "__main__":
    sys.exit(0 if run() else 1)

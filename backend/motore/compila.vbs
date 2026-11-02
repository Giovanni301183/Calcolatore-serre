' Compila una COPIA del master Excel. Uso: cscript //nologo compila.vbs <master.xls> <uscita.xls> <celle.txt> <riepilogo.txt>
' celle.txt: righe "FOGLIO<TAB>CELLA<TAB>N|S<TAB>valore"  (N = numero, S = testo)
Dim xl, wb, fso, f, line, p, ws, out, r, c, v, maxR, totRow, desc
totRow = 0
Set fso = CreateObject("Scripting.FileSystemObject")
fso.CopyFile WScript.Arguments(0), WScript.Arguments(1), True
Set xl = CreateObject("Excel.Application")
xl.DisplayAlerts = False
xl.Visible = False
Set wb = xl.Workbooks.Open(WScript.Arguments(1))
Set f = fso.OpenTextFile(WScript.Arguments(2), 1, False, -1)
Do Until f.AtEndOfStream
  line = f.ReadLine
  p = Split(line, vbTab)
  If UBound(p) >= 3 Then
    Set ws = wb.Worksheets(p(0))
    If p(2) = "N" Then
      ws.Range(p(1)).Value = CDbl(Replace(p(3), ".", Mid(CStr(1.5), 2, 1)))
    Else
      ws.Range(p(1)).Value = p(3)
    End If
  End If
Loop
f.Close
xl.CalculateFull
' riepilogo: righe con "TOTALE" o "Tot" nel foglio Analisi Pesi (testo e valori della riga)
Set out = fso.CreateTextFile(WScript.Arguments(3), True, True)
Set ws = wb.Worksheets("Analisi Pesi")
For r = 80 To 140
  If InStr(1, ws.Cells(r, 9).Text, "PESO TOTALE", 1) > 0 And InStr(1, ws.Cells(r, 13).Text, "Tot", 1) > 0 Then
    out.WriteLine "peso_kg" & vbTab & ws.Cells(r, 14).Value
    out.WriteLine "riga" & vbTab & r
    ' tutte le celle numeriche della riga totali con l'intestazione sopra (r-1) o il testo a destra (r)
    For c = 15 To 40
      If ws.Cells(r, c).HasFormula Then
        out.WriteLine "col" & c & vbTab & ws.Cells(r, c).Value & vbTab & ws.Cells(r - 1, c).Text & vbTab & ws.Cells(r, c + 1).Text & vbTab & ws.Cells(r, c).Formula
      End If
    Next
    totRow = r
    Exit For
  End If
Next
' righe di costo della struttura: costo €/kg (col X=24), prezzo €/kg (col Z=26), prezzo riga (col AB=28)
out.WriteLine "ricarico" & vbTab & ws.Cells(7, 26).Value
desc = ""
If totRow > 0 Then
  For r = 15 To totRow - 1
    If Trim(ws.Cells(r, 1).Text) <> "" And Trim(ws.Cells(r, 2).Text) <> "" Then desc = ws.Cells(r, 2).Text
    v = ws.Cells(r, 28).Value
    If IsNumeric(v) And Not IsEmpty(v) Then
      If CDbl(v) <> 0 Then
        out.WriteLine "voce" & vbTab & r & vbTab & desc & vbTab & ws.Cells(r, 24).Value & vbTab & ws.Cells(r, 26).Value & vbTab & v
      End If
    End If
  Next
End If
' pezzi speciali: descrizione, quantità, prezzo unitario, costo totale
Set ws = wb.Worksheets("Pezzi Speciali")
For r = 10 To 45
  If InStr(1, ws.Cells(r, 5).Text, "TOTALE", 1) > 0 Then
    out.WriteLine "ps_totale" & vbTab & ws.Cells(r, 7).Value
    Exit For
  End If
  If IsNumeric(ws.Cells(r, 1).Value) And Trim(ws.Cells(r, 2).Text) <> "" Then
    out.WriteLine "ps" & vbTab & ws.Cells(r, 2).Text & vbTab & ws.Cells(r, 3).Value & vbTab & ws.Cells(r, 4).Value & vbTab & ws.Cells(r, 7).Value
  End If
Next
out.Close
wb.Save
wb.Close False
xl.Quit
WScript.Echo "ok"

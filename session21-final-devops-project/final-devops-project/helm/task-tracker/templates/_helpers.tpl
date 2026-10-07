{{- define "tt.name" -}}{{ .Release.Name }}{{- end -}}
{{- define "tt.labels" -}}
app.kubernetes.io/name: task-tracker
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
{{- define "tt.selector" -}}
app.kubernetes.io/name: task-tracker
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "tt.secretName" -}}
{{- if .Values.secret.existingSecret -}}{{ .Values.secret.existingSecret }}{{- else -}}{{ include "tt.name" . }}-secret{{- end -}}
{{- end -}}

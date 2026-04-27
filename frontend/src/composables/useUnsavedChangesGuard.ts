import type { Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm'
import { useI18n } from 'vue-i18n'

export function useUnsavedChangesGuard(
  dialogVisible: Ref<boolean>,
  isDirty: () => boolean,
  options?: { withRouteLeaveGuard?: boolean },
): (val: boolean) => void {
  const { t } = useI18n()
  const confirm = useConfirm()

  function onCloseDialog(val: boolean): void {
    if (val) {
      dialogVisible.value = true
      return
    }
    if (isDirty()) {
      confirm.require({
        message: t('common.unsaved_changes_confirm'),
        header: t('common.unsaved_changes'),
        icon: 'pi pi-exclamation-triangle',
        acceptProps: { severity: 'warn', label: t('common.discard') },
        rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
        accept: () => {
          dialogVisible.value = false
        },
      })
    } else {
      dialogVisible.value = false
    }
  }

  if (options?.withRouteLeaveGuard) {
    onBeforeRouteLeave((to, from, next) => {
      if (dialogVisible.value && isDirty()) {
        confirm.require({
          message: t('common.unsaved_changes_confirm'),
          header: t('common.unsaved_changes'),
          icon: 'pi pi-exclamation-triangle',
          acceptProps: { severity: 'warn', label: t('common.discard') },
          rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
          accept: () => {
            dialogVisible.value = false
            next()
          },
          reject: () => {
            next(false)
          },
        })
      } else {
        next()
      }
    })
  }

  return onCloseDialog
}

<script setup lang="ts">
defineProps<{
  data: Record<string, any>[]
  columns: { key: string; label: string }[]
}>()
</script>

<template>
  <div
    class="overflow-x-auto rounded-xl border"
    :style="{ borderColor: 'var(--border-color)' }"
  >
    <table class="data-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="whitespace-nowrap"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, idx) in data"
          :key="idx"
          :style="{
            borderBottom: '1px solid var(--border-color)',
          }"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            class="whitespace-nowrap"
          >
            {{ row[col.key] }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

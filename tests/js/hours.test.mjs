import { test } from 'node:test';
import assert from 'node:assert/strict';
import { chicagoNow, formatTime, statusFor } from '../../static/js/hours.js';

const HQ = { mon: ['08:00', '20:00'], tue: ['08:00', '20:00'], wed: ['08:00', '20:00'], thu: ['08:00', '20:00'], fri: ['08:00', '20:00'], sat: ['08:00', '17:30'] };
const SOUTH = { mon: ['09:30', '18:00'], tue: ['09:30', '18:00'], wed: ['09:30', '18:00'], thu: ['09:30', '18:00'], fri: ['09:30', '18:00'], sat: ['09:00', '15:00'] };
const at = (day, h, m = 0) => ({ day, minutes: h * 60 + m });

test('formatTime drops :00 and uses 12-hour clock', () => {
  assert.equal(formatTime('08:00'), '8 AM');
  assert.equal(formatTime('09:30'), '9:30 AM');
  assert.equal(formatTime('17:30'), '5:30 PM');
  assert.equal(formatTime('20:30'), '8:30 PM');
  assert.equal(formatTime('12:00'), '12 PM');
  assert.equal(formatTime('00:00'), '12 AM');
});

test('open during hours', () => {
  assert.deepEqual(statusFor(HQ, at(2, 18, 30)), { open: true, label: 'Open, closes 8 PM' });
});

test('before opening today', () => {
  assert.deepEqual(statusFor(SOUTH, at(3, 7)), { open: false, label: 'Closed, opens 9:30 AM' });
});

test('exactly at closing time counts as closed', () => {
  assert.deepEqual(statusFor(HQ, at(5, 20)), { open: false, label: 'Closed, opens tomorrow 8 AM' });
});

test('Saturday after close skips Sunday', () => {
  assert.deepEqual(statusFor(HQ, at(6, 18)), { open: false, label: 'Closed, opens Monday 8 AM' });
});

test('Sunday with no published hours', () => {
  assert.deepEqual(statusFor(SOUTH, at(0, 12)), { open: false, label: 'Closed, opens tomorrow 9:30 AM' });
});

test('chicagoNow reads Chicago time across the DST change (Nov 1 2026)', () => {
  assert.deepEqual(chicagoNow(new Date('2026-10-30T13:00:00Z')), { day: 5, minutes: 480 }); // Fri 8:00 CDT
  assert.deepEqual(chicagoNow(new Date('2026-11-02T14:00:00Z')), { day: 1, minutes: 480 }); // Mon 8:00 CST
  assert.deepEqual(chicagoNow(new Date('2026-11-01T06:30:00Z')), { day: 0, minutes: 90 });  // 1:30 CDT
  assert.deepEqual(chicagoNow(new Date('2026-11-01T07:30:00Z')), { day: 0, minutes: 90 });  // 1:30 CST
});

test('midnight is minute 0, not 1440', () => {
  assert.deepEqual(chicagoNow(new Date('2026-10-07T05:00:00Z')), { day: 3, minutes: 0 }); // Wed 00:00 CDT
});

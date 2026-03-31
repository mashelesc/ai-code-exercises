/**
 * Calculates the average and highest value of a numeric field across all users.
 *
 * @param {Object[]} userData - Array of user objects.
 * @param {string} field - The numeric field to aggregate (e.g. 'age', 'income').
 * @returns {{ average: number, highest: number }}
 */
function calculateFieldStatistics(userData, field) {
  const total = userData.reduce((sum, user) => sum + user[field], 0);
  const highest = Math.max(...userData.map(user => user[field]));

  return {
    average: total / userData.length,
    highest,
  };
}

/**
 * Calculates average and highest values for age, income, and score across all users.
 *
 * @param {Object[]} userData - Array of user objects, each with numeric 'age', 'income', 'score'.
 * @returns {{ age: Object, income: Object, score: Object }} - Each key maps to { average, highest }.
 * @throws {Error} If userData is empty or undefined.
 */
function calculateUserStatistics(userData) {
  if (!userData || userData.length === 0) {
    throw new Error('userData must be a non-empty array');
  }

  const fields = ['age', 'income', 'score'];

  return Object.fromEntries(
    fields.map(field => [field, calculateFieldStatistics(userData, field)])
  );
}
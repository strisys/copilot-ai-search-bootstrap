import { expect } from 'chai';
import { run } from '../search.js';
describe('AzureSearch', () => {
    describe('run', function () {
        it('should run the search', async () => {
            // Assemble/Arrange
            const query = 'What is Azure?';
            // Assert
            const result = (await run(query));
            expect(result).to.be.an('string');
        });
    });
});
//# sourceMappingURL=search.spec.js.map
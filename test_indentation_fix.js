// 들여쓰기 수정 테스트 스크립트
// 브라우저 콘솔에서 실행하여 들여쓰기 값 확인

console.log('=== 들여쓰기 수정 테스트 ===');

// CSS 커스텀 프로퍼티 값 확인
const rootStyle = getComputedStyle(document.documentElement);
console.log('CSS 변수 값:');
console.log('  --file-tree-indent-base:', rootStyle.getPropertyValue('--file-tree-indent-base'));
console.log('  --file-tree-indent-mobile:', rootStyle.getPropertyValue('--file-tree-indent-mobile'));
console.log('  --file-tree-indent-small:', rootStyle.getPropertyValue('--file-tree-indent-small'));
console.log('  --file-tree-max-depth:', rootStyle.getPropertyValue('--file-tree-max-depth'));

// 현재 화면 크기 확인
console.log('\n현재 화면 정보:');
console.log('  화면 너비:', window.innerWidth + 'px');
console.log('  예상 들여쓰기 크기:', 
  window.innerWidth <= 480 ? '4px (초소형)' :
  window.innerWidth <= 768 ? '6px (모바일)' : '8px (데스크톱)'
);

// 실제 적용된 file-tree-node 요소들 확인
const fileTreeNodes = document.querySelectorAll('.file-tree-node');
console.log('\n실제 적용된 들여쓰기:');
fileTreeNodes.forEach((node, index) => {
  if (index < 10) { // 처음 10개만 확인
    const marginLeft = node.style.marginLeft;
    const computedMargin = getComputedStyle(node).marginLeft;
    console.log(`  노드 ${index}: 인라인=${marginLeft}, 계산됨=${computedMargin}`);
  }
});

// 16px 들여쓰기가 남아있는지 확인
const oldIndentNodes = Array.from(fileTreeNodes).filter(node => 
  node.style.marginLeft.includes('16px') || 
  getComputedStyle(node).marginLeft.includes('16px')
);
console.log('\n16px 들여쓰기 잔존 여부:', oldIndentNodes.length > 0 ? '있음 ❌' : '없음 ✅');

if (oldIndentNodes.length > 0) {
  console.log('16px 들여쓰기가 남은 노드들:', oldIndentNodes);
}

console.log('\n=== 테스트 완료 ===');